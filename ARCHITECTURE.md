# ARCHITECTURE - Multi-Stack AI Agent Platform

**Datum:** 2025-11-26
**Versie:** 4.0 (Multi-Stack Platform Vision)
**Status:** Fase 1-3 Compleet | Week 52 LLM Council | Week 53 Evolution + ProjectProfile | Week 54+ Multi-Stack Platform

---

## Visie in een zin

**Een AI-powered multi-stack platform waar agents automatisch werk analyseren, opdelen, schatten en uitvoeren - terwijl jij gewoon in project.md blijft werken.**

---

## Architectuur: De Lagen

```
+---------------------------------------------------------------------+
|  MENS (Jij)                                                          |
|  - Editeert project.md in vim/VSCode                                 |
|  - Gebruikt project-manager.html UI                                  |
|  - Beoordeelt agent voorstellen                                      |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  MARKDOWN (Bron van Waarheid)                                        |
|  - project.md = Epic -> Feature -> Story -> Task                     |
|  - Git versie controle                                               |
|  - Mens-leesbaar en editeerbaar                                      |
+---------------------------------------------------------------------+
                            | (Sync Engine)
+---------------------------------------------------------------------+
|  DATABASE (Query & Analytics)                                        |
|  - PostgreSQL met hierarchische structuur                            |
|  - Snel doorzoekbaar voor agents                                     |
|  - Metrics en rapportages                                            |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  BACKEND API (FastAPI)                                               |
|  - 196+ REST endpoints                                               |
|  - WebSocket voor real-time updates                                  |
|  - Authentification (JWT)                                            |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  3-LAAGS AGENT ARCHITECTUUR (Multi-Stack Platform)                   |
|                                                                      |
|  Laag 1: Core Agents (10 - Cross-Stack)                              |
|  - Felix, Quinn, Betty, Eliza, Diana, Marcus, Tessa, Miguel,         |
|    Peter, Paul                                                       |
|                                                                      |
|  Laag 2: Stack Agent Templates (Per Project)                         |
|  - BackendDev_{stack}, FrontendDev_{stack}, CodeReviewer_{stack},    |
|    SecurityAuditor_{stack}, Tester_{stack}                           |
|                                                                      |
|  Laag 3: Platform Agents (Meta-niveau)                               |
|  - ObservabilityEngineer, PromptEngineer                             |
|  - (Later: IncidentResponder, ContextManager)                        |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  MULTI-MODEL LAYER (Provider Registry)                               |
|  - Ollama (Local): qwen2.5-coder, deepseek-r1, codellama, mistral   |
|  - Codex CLI: gpt-5.1-codex-max, o3 (complex analysis)              |
|  - Claude CLI: Haiku (fast), Sonnet (balanced), Opus (deep)         |
|  - Model Router: Task complexity -> Optimal model                    |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  INTELLIGENCE LAYER                                                  |
|  - Function Point Calculator (IFPUG)                                 |
|  - Story Point Estimator (PERT)                                      |
|  - Work Type Router (9 workflows)                                    |
|  - Quality Gates System (42 validation rules)                        |
|  - LLM Council (6-model consensus)                                   |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  OBSERVABILITY LAYER (Agent Behavior Monitoring)                     |
|  - Action logging (elke agent actie)                                 |
|  - Decision tracing (welke keuzes, waarom)                           |
|  - Performance metrics (success rate, duration, cost)                |
|  - Pattern detection (wat werkt, wat niet)                           |
+---------------------------------------------------------------------+
                            |
+---------------------------------------------------------------------+
|  SELF-EVOLUTION LAYER                                                |
|  - Self-Questioning: Automatische taak generatie                     |
|  - Self-Navigating: Ervaring-geleide exploratie                      |
|  - Self-Attributing: Credit assignment & outcome analysis            |
|  - Experience Store: ChromaDB (5 collections)                        |
+---------------------------------------------------------------------+
```

---

## Architectuur Documenten (Detail)

| Document | Beschrijving | Status |
|----------|--------------|--------|
| **[Self-Evolution Layer](./docs/architecture/self-evolution.md)** | AgentEvolver integratie, ChromaDB, self-questioning | Week 17-26 |
| **[Project Profiles](./docs/architecture/project-profiles.md)** | Dynamic agent configuration per project size/focus | Week 53 COMPLETE |
| **[Validation Framework](./docs/architecture/validation-framework.md)** | 5-fase validatie pipeline, iteratie loops | Week 17-26 |
| **[Quality Gates System](./docs/architecture/quality-gates.md)** | 28 checks, 8 categorien, pre-commit automation | Week 10-12 COMPLETE |
| **[A/B Testing Framework](./docs/architecture/ab-testing.md)** | Multi-variant experimentation, statistical analysis | Week 51 COMPLETE |
| **[LLM Council](./docs/architecture/llm-council.md)** | Multi-model consensus, 3-stage process | Week 52 COMPLETE |
| **[Continuous Evolution](./docs/architecture/continuous-evolution.md)** | Trend analysis, gradual rollout, auto-scheduling | Week 53 COMPLETE |
| **[Multi-Stack Platform](./docs/architecture/multi-stack-platform.md)** | Provider registry, stack templates, observability | Week 54-58 PLANNED |

---

## Multi-Stack Platform Vision (Week 54+)

### Nieuwe Architectuur Componenten

#### 1. Provider Registry (Multi-LLM Abstractie) - IMPLEMENTED

```python
# Located in: backend/app/providers/

class LLMProvider:
    name: str           # "ollama", "codex", "claude"
    tier: str           # "free", "fast", "balanced", "deep"
    cost_input: float   # per million tokens
    cost_output: float  # per million tokens
    is_local: bool      # True for Ollama
    is_active: bool
    config: Dict        # model-specific settings

# Implemented Providers:
# - OllamaProvider: Local, free, qwen2.5-coder/deepseek-r1/codellama/mistral
# - CodexProvider: OpenAI CLI, gpt-5.1-codex-max for complex analysis

# Model Routing Strategy
TASK_TO_MODEL = {
    "simple_generation": "ollama/qwen2.5-coder:7b",    # Free, local
    "quick_fix": "ollama/qwen2.5-coder:7b",            # Free, fast
    "documentation": "ollama/mistral:latest",          # Good at prose
    "debugging": "ollama/codellama:latest",            # Specialized
    "code_review": "codex/gpt-5.1-codex-max",          # Deep analysis
    "refactoring": "codex/gpt-5.1-codex-max",          # Structural
    "architecture": "codex/gpt-5.1-codex-max",         # Multi-file reasoning
    "security_audit": "codex/gpt-5.1-codex-max",       # Critical analysis
    "complex_analysis": "codex/gpt-5.1-codex-max",     # Deep investigation
}
```

#### 2. Stack Agent Factory

```python
# Template-based agent instantiation per tech-stack
STACK_AGENTS = {
    "python": ["BackendDev_py", "CodeRev_py", "SecAudit_py", "Tester_py"],
    "javascript": ["BackendDev_js", "FrontendDev_js", "CodeRev_js", "SecAudit_js", "Tester_js"],
    "go": ["BackendDev_go", "CodeRev_go", "SecAudit_go", "Tester_go"],
    "rust": ["BackendDev_rs", "CodeRev_rs", "SecAudit_rs", "Tester_rs"],
}

def create_stack_agent(stack: str, role: str, project_id: UUID) -> StackAgent:
    """Instantiate stack-specific agent from template."""
    template = AGENT_TEMPLATES[role]
    return StackAgent(
        name=f"{role}_{stack}",
        stack=stack,
        project_id=project_id,
        prompt_template=template.get_prompt(stack),
        model=template.get_model(stack),
        capabilities=template.get_capabilities(stack),
    )
```

#### 3. Observability System (Agent Behavior Monitoring)

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

#### 4. PromptEngineer + Meta-Prompting

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
        return await self.enhance_prompt(
            original_prompt=agent.base_prompt,
            task_context=task.context,
            performance_insights=metrics,
            proven_patterns=patterns,
        )

    async def evaluate_and_update(self, task_result: TaskResult):
        """A/B test prompt variations and roll out improvements."""
        if task_result.success:
            await self.store_successful_pattern(task_result)
        else:
            await self.analyze_failure(task_result)
```

---

## Current Status

### Production Metrics

| Metric | Value |
|--------|-------|
| **API Endpoints** | 196+ |
| **Database Tables** | 49 |
| **Dashboards** | 14 |
| **Agents** | 10 Core + Stack Templates |
| **Ollama Models** | 6 (~25GB) |
| **Quality Checks** | 42 rules, 8 categories |
| **ChromaDB Collections** | 5 |
| **Test Coverage** | 130+ comprehensive tests |

### Phase Status

```
Backend:           [####################] 100% - 196 endpoints
Frontend:          [####################] 100% - 14 dashboards
Sync Engine:       [####################] 100% - Fase 1
Agents:            [####################] 100% - 10 agents
Quality Gates:     [####################] 100% - Fase 3 Week 10-12
A/B Testing:       [####################] 100% - Week 51
LLM Council:       [####################] 100% - Week 52
Continuous Evol:   [####################] 100% - Week 53
Multi-Stack:       [                    ]   0% - Week 54-58 PLANNED
```

---

## Quick Links

### Core Documents

- **[PROJECT_STATUS_SUMMARY.md](./PROJECT_STATUS_SUMMARY.md)** - Single entry point (START HERE)
- **[ROADMAP.md](./ROADMAP.md)** - 40-week planning master
- **[AGENTS.md](./AGENTS.md)** - AI agent system reference
- **[README.md](./README.md)** - Project introduction

### Architecture Details

- **[docs/architecture/](./docs/architecture/)** - All architecture detail documents
- **[docs/reviews/](./docs/reviews/)** - Platform reviews and analyses
- **[docs/roadmap/](./docs/roadmap/)** - Phase-specific roadmaps

---

## Related Documentation

- **Full Agent Specifications**: `backend/agents/AGENT_SPECIFICATIONS.md`
- **Integration Guide**: `backend/agents/INTEGRATION_GUIDE.md`
- **LLM Configuration**: `backend/agents/LLM_CONFIGURATION.md`
- **Quality Gates Config**: `docs/quality/QUALITY_GATE_CONFIGURATION.md`

---

**Last Updated**: 2025-11-26
**Version**: 4.0 (Multi-Stack Platform Vision)
**Status**: Active Development
