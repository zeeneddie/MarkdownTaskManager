# 🤖 AGENTS - AI Agent System Reference

**Doel**: Complete agent system documentation op één plek
**Doelgroep**: Developers working with agents
**Last Updated**: 2025-11-21 (AgentEvolver Integration Added)

---

## 🎯 Quick Overview

**10 Specialized AI Agents** - 100% Local Execution (Ollama)
**9 Work Type Workflows** - Intelligent routing
**4 Scrum Ceremonies** - Automated
**16 SuperClaude Commands** - Domain expertise
**Quality Gates** - Integrated validation
**🧬 Self-Evolution** - Week 17-26: Agents die zichzelf verbeteren!

---

## 📋 The 10 Agents

### Core Agents (8)

#### 1. Felix - Feature Architect
- **Role**: Architecture & feature design
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: System design, API design, work breakdown
- **Workflows**: NEW_FEATURE, PROJECT_DEFINITION

#### 2. Marcus - Maintenance Specialist  
- **Role**: Code maintenance & tech debt
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Refactoring, dependency updates, code health
- **Workflows**: MAINTENANCE

#### 3. Quinn - Quality Inspector
- **Role**: Quality assurance & security
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: Code review, security audits, quality gates
- **Workflows**: QUALITY_AUDIT, QUALITY_IMPROVEMENT

#### 4. Betty - Bug Hunter
- **Role**: Bug investigation & fixing
- **LLM**: codellama:latest (local)
- **Specialties**: Debugging, root cause analysis, error handling
- **Workflows**: BUG

#### 5. Eliza - Estimation Engine
- **Role**: Effort estimation & complexity analysis
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: Function points, story points, ML-based estimation
- **Workflows**: All (provides estimates)

#### 6. Tessa - Test Engineer
- **Role**: Test automation & coverage
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Unit tests, E2E tests, test strategy
- **Workflows**: TESTING, all workflows (provides test coverage)

#### 7. Miguel - Migration Architect
- **Role**: Migration & platform upgrades
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Tech stack migrations, data migrations
- **Workflows**: MIGRATION

#### 8. Diana - Documentation Writer
- **Role**: Technical documentation
- **LLM**: mistral:latest (local)
- **Specialties**: API docs, architecture docs, user guides
- **Workflows**: All (provides documentation)

### Management Agents (2)

#### 9. Peter - Product Owner
- **Role**: Requirements & product vision
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: User stories, business analysis, prioritization
- **Workflows**: PROJECT_DEFINITION

#### 10. Paul - Project Lead
- **Role**: Project planning & coordination
- **LLM**: qwen2.5:7b (local)
- **Specialties**: Resource allocation, sprint planning, risk management
- **Workflows**: PROJECT_DEFINITION

### Nieuwe rollen (in evaluatie)

#### UX Designer (Nieuw)
- **Role**: UX research & interaction design
- **LLM**: local (tbd)
- **Specialties**: user flows, wireframes, usability checks
- **Status**: gedefinieerd, nog te evalueren

#### Frontend Developer (Nieuw)
- **Role**: UI implementatie & performance
- **LLM**: local (tbd)
- **Specialties**: Blazor, HTML/CSS, JS/TS, componenten, styling, build/optimalisatie
- **Status**: gedefinieerd, nog te evalueren

#### Backend Developer (Nieuw)
- **Role**: API/DB/services implementatie
- **LLM**: local (tbd)
- **Specialties**: .NET Core/C#, CQRS, API design, data access, reliability
- **Status**: gedefinieerd, nog te evalueren

**Aanbevolen stack voor Frontend/Backend (richtlijnen):**
- Frontend: Blazor, HTML/CSS, JS/TS; component libs naar keuze; bundling/build volgens project.
- Backend: ASP.NET Core (minimal APIs), CQRS (bv. MediatR), EF Core, SQL Server, Serilog/Seq, Swagger/OpenAPI, xUnit/FluentAssertions, FluentValidation, Docker/Compose.
- Git workflow: feature branches, korte-lived branches, PR-review, consistente branch/commit conventies.

#### Integratie Specialist (Nieuw)
- **Role**: System integraties & interfacing
- **LLM**: local (tbd)
- **Specialties**: externe APIs, message flows, contract testing
- **Status**: gedefinieerd, nog te evalueren

---

## 🧬 Self-Evolution Capabilities (Week 17-26)

**Bron:** github.com/zeeneddie/AgentEvolver
**Status:** Goedgekeurd 2025-11-21

### Alle Agents Worden Zelf-Evoluerend!

Vanaf Week 17 krijgen alle 10 agents de volgende capabilities:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ SELF-QUESTIONING │     │ SELF-NAVIGATING  │     │ SELF-ATTRIBUTING │
│                  │     │                  │     │                  │
│ "Wat moet ik nog │     │ "Hoe deed ik dit │     │ "Welke stappen   │
│  leren?"         │     │  eerder goed?"   │     │  waren cruciaal?"|
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Evolution Capabilities per Agent

| Agent | Self-Questioning | Self-Navigating | Self-Attributing |
|-------|------------------|-----------------|------------------|
| **Felix** | Genereert edge-case specs | "Microservices werkte bij project X" | "Design Y leidde tot succes" |
| **Marcus** | Identificeert tech debt scenarios | "Refactoring pattern A werkt goed" | "Maintenance actie Z had impact" |
| **Quinn** | Creëert security test cases | "SQL injection check ving 80% bugs" | "Gate B ving 90% echte issues" |
| **Betty** | Simuleert nieuwe bug types | "Debugging strategie X werkte" | "Root cause was altijd laag Y" |
| **Eliza** | Test schattingen op hist. data | "Bij features A was schatting te laag" | "Factor Z werd onderschat" |
| **Tessa** | Genereert test edge cases | "Test strategie B was effectief" | "Test C ving bug D" |
| **Miguel** | Simuleert migratierisico's | "Migratie strategie E werkte" | "Stap F was kritiek" |
| **Diana** | Genereert doc templates | "Format G was populair" | "Section H miste vaak" |
| **Peter** | Genereert requirement variations | "User story format I werkte" | "Requirement J was incompleet" |
| **Paul** | Simuleert planning scenarios | "Sprint planning K werkte" | "Risico L werd gemist" |

### Evolving Agent Interface

```typescript
interface EvolvingAgent extends Agent {
  // Bestaande capabilities
  name: string;
  role: string;
  llm: OllamaModel;
  specialties: string[];

  // NIEUW: Evolution capabilities (Week 17+)
  evolution: {
    // Raadpleeg ervaring voor beslissingen
    consultExperience(context: TaskContext): Promise<Guidance>;

    // Log outcome na taak completion
    logOutcome(result: TaskResult): Promise<void>;

    // Ontvang feedback voor verbetering
    receiveFeedback(attribution: Attribution): Promise<void>;

    // Performance metrics
    getPerformanceMetrics(): PerformanceMetrics;
  };

  // NIEUW: Evolution parameters
  evolutionConfig: {
    learningRate: number;           // Hoe snel past agent zich aan?
    experienceWeight: number;       // Hoeveel weegt ervaring mee?
    explorationRate: number;        // Hoeveel experimenteert agent?
    attributionDepth: number;       // Hoe diep analyseert agent outcomes?
  };
}
```

### Experience Store (5 Nieuwe ChromaDB Collections)

```
ChromaDB Collections (Week 17+):
├── agent_experiences         # Cross-task learnings per agent
├── successful_patterns       # Wat werkte goed? (herbruikbaar)
├── failure_analysis          # Wat ging fout en waarom?
├── estimation_accuracy       # Schatting vs werkelijk per agent
└── quality_metrics           # Code quality over tijd
```

### Success Metrics (Targets Week 26)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent Success Rate | +15% | Before/after comparison |
| Estimation Accuracy | +20% | Predicted vs actual |
| Code Quality | +10% | Quality gate scores |
| Experience Relevance | >80% | Semantic similarity |
| Self-generated Tasks | >100/week | Task generation count |

### Safety Guardrails (Balanced Mode)

| Automatisch Toegestaan | Human Approval Vereist |
|------------------------|------------------------|
| Experience logging | Policy changes |
| Pattern matching | Nieuwe patterns toevoegen |
| Outcome tracking | Cross-workflow regels |
| Minor weight updates | Grote gedragswijzigingen |

**Rollback Triggers:**
- Success rate drop >10%
- Quality score drop >15%
- Estimation error increase >20%

---

## ✅ Validation Capabilities (Week 17-26)

**Bron:** github.com/zeeneddie/context-engineering-intro
**Status:** Goedgekeurd 2025-11-21

### Alle Agents Krijgen Validatie Loops!

Vanaf Week 17 itereert elke agent automatisch tot code validatie slaagt:

```
┌─────────────────────────────────────────────────────────┐
│                 VALIDATION ITERATION LOOP               │
│                                                         │
│  Generate Code → Validate → Failed?                     │
│       ↑                         │                       │
│       │                         ↓                       │
│       └────── Fix Issues ←── Yes                        │
│                                 │                       │
│                                 ↓ No                    │
│                           ✅ Complete                   │
└─────────────────────────────────────────────────────────┘
```

### 5-Fase Validatie Pipeline

| Fase | Tool (Python) | Tool (TypeScript) | Wat valideert het? |
|------|---------------|-------------------|-------------------|
| **1. LINTING** | ruff | eslint | Syntax errors, code smells |
| **2. TYPE CHECK** | mypy | tsc | Type correctness |
| **3. STYLE** | black | prettier | Code formatting |
| **4. UNIT TESTS** | pytest | jest | Functionele correctheid |
| **5. E2E** | pytest+httpx | jest+supertest | Integration werkt |

### Validatie per Agent

| Agent | Validatie Fasen | Max Iterations | Speciale Regels |
|-------|-----------------|----------------|-----------------|
| **Felix** | 1-5 (alle) | 3 | 80% coverage vereist |
| **Marcus** | 1-2, 4 | 2 | 70% coverage |
| **Quinn** | 1-3 | 1 | Report only (audit) |
| **Betty** | 1, 4-5 | 3 | Regression test vereist |
| **Eliza** | - | - | Valideert schattingen tegen historisch |
| **Tessa** | 4 | 1 | Meta-validatie (tests testen) |
| **Miguel** | 5 only | 2 | E2E kritiek voor migraties |
| **Diana** | 1 | 1 | Template validatie |
| **Peter** | 1 | 1 | Requirement format check |
| **Paul** | - | - | Planning validation |

### Validating Agent Interface

```typescript
interface ValidatingAgent extends EvolvingAgent {
  // Inherited from EvolvingAgent
  evolution: EvolutionCapabilities;

  // NIEUW: Validation capabilities (Week 17+)
  validation: {
    // Run validation pipeline
    runValidation(code: string): Promise<ValidationResult>;

    // Iterate until valid
    iterateUntilValid(
      code: string,
      maxIterations: number
    ): Promise<ValidatedCode>;

    // Request fix for validation errors
    requestFix(
      code: string,
      errors: ValidationError[]
    ): Promise<string>;

    // Get validation config for workflow
    getValidationConfig(): ValidationConfig;
  };

  // Validation configuration
  validationConfig: {
    phases: ValidationPhase[];
    maxIterations: number;
    stopOnFirstFailure: boolean;
    requiredCoverage?: number;
    regressionTestRequired?: boolean;
  };
}
```

### Synergie: Evolution + Validation

**Perfecte Combinatie!** Validation integreert met Self-Evolution:

| Self-Evolution | Validation Integration |
|----------------|----------------------|
| **Self-Questioning** | Genereer validatie test cases automatisch |
| **Self-Navigating** | Leer van eerdere validatie successen |
| **Self-Attributing** | Track welke validaties vaak falen |

```typescript
interface ValidationExperience {
  agent_id: string;
  workflow_type: WorkType;
  validation_attempts: number;
  failed_phases: ValidationPhase[];
  fix_strategies_used: FixStrategy[];
  final_result: 'SUCCESS' | 'MAX_ITERATIONS' | 'MANUAL';
  lessons_learned: string[];
}
```

### Validation Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **First-Time Success** | >80% | Code passes validation first try |
| **Iteration Success** | >95% | Code passes within 3 iterations |
| **Coverage** | >80% | Unit test coverage |
| **Validation Time** | <5 min | Full pipeline execution |

### Impact

> **"Als /validate slaagt, moet de gebruiker 100% vertrouwen hebben dat de applicatie correct werkt in productie."**

| Zonder Validation | Met Validation |
|-------------------|----------------|
| "Hopelijk werkt het" | Iteratie tot succes |
| 60% zekerheid | 100% zekerheid |
| Handmatige fixes | Automatische fix loop |
| Reactief | 5-fase pipeline |

---

## 🧠 Self-Questioning Implementation (Week 23-24)

**Status:** ✅ COMPLETE
**Doel:** Agents genereren zelf training tasks op basis van prestatie-analyse

### 5-Stage Training Pipeline

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ DATA COLLECTION  │ --> │ SELF-QUESTIONING │ --> │ TASK GENERATION  │
│ Gather metrics   │     │ Generate Qs      │     │ Create tasks     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                                                   │
        └──────────────────────────────────────────────────┘
                                   │
                    ┌──────────────────────────┐
                    │                          │
        ┌──────────────────┐     ┌──────────────────┐
        │ TRAINING EXEC    │ --> │ EVALUATION       │
        │ Execute tasks    │     │ Generate insights│
        └──────────────────┘     └──────────────────┘
```

### Question Categories

| Category | Description | Example |
|----------|-------------|---------|
| `performance_gap` | Where am I underperforming? | "Why do I miss edge cases in auth?" |
| `edge_case` | What edge cases am I missing? | "What unusual inputs could break this?" |
| `knowledge_gap` | What don't I know? | "How do microservices handle X?" |
| `skill_improvement` | How can I do this better? | "What patterns improve reliability?" |
| `pattern_discovery` | What patterns should I learn? | "What worked in similar projects?" |

### Self-Questioning Engine Interface

```typescript
interface SelfQuestioningEngine {
  // Generate questions from performance data
  generateQuestions(input: {
    agentId: AgentName;
    performanceData: PerformanceData;
    recentTasks: Task[];
    maxQuestions: number;
  }): Promise<SelfQuestion[]>;

  // Create synthetic training tasks
  generateTrainingTasks(input: {
    agentId: AgentName;
    questions: SelfQuestion[];
    maxTasks: number;
  }): Promise<SyntheticTask[]>;

  // Discover edge cases from patterns
  discoverEdgeCases(input: {
    agentId: AgentName;
    recentTasks: Task[];
    failureAnalysis: FailureAnalysis;
  }): Promise<EdgeCase[]>;

  // Run complete session
  runSession(input: SessionInput): Promise<QuestioningSession>;
}
```

### Training Modes

| Mode | Questions | Tasks | Focus |
|------|-----------|-------|-------|
| **Balanced** | 5-10 | 3-5 | Steady improvement |
| **Intensive** | 10-20 | 8-15 | Rapid skill building |
| **Focused** | 2-5 | 1-3 | Targeted gap closure |

### Agent-Specific Question Templates

| Agent | Primary Categories | Example Questions |
|-------|-------------------|-------------------|
| **Felix** | Architecture, Design Patterns | "How handle circular dependencies?" |
| **Marcus** | Tech Debt, Refactoring | "What's the impact of skipping tests?" |
| **Quinn** | Security, Vulnerabilities | "What SQL injection variations exist?" |
| **Betty** | Debugging, Root Cause | "How do race conditions manifest?" |
| **Eliza** | Estimation, Complexity | "Why was this estimate too low?" |
| **Tessa** | Testing, Coverage | "What edge cases did I miss?" |
| **Miguel** | Migration, Compatibility | "What breaking changes occur?" |
| **Diana** | Documentation, Clarity | "Why was this doc confusing?" |
| **Peter** | Requirements, Scope | "What requirements were ambiguous?" |
| **Paul** | Planning, Risk | "What risks were underestimated?" |

### Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `agents/lib/selfQuestioningEngine.ts` | Core engine | ~800 |
| `agents/workflows/selfTrainingWorkflow.ts` | Training pipeline | ~500 |
| `app/api/self_questioning.py` | Python API | ~500 |
| `frontend/self-improvement-dashboard.html` | Dashboard UI | ~750 |

### API Endpoints

```
GET  /api/self-questioning/sessions          # List sessions
POST /api/self-questioning/sessions          # Start session
GET  /api/self-questioning/sessions/{id}     # Session details
POST /api/self-questioning/sessions/{id}/pause   # Pause
POST /api/self-questioning/sessions/{id}/resume  # Resume
GET  /api/self-questioning/metrics           # All agent metrics
GET  /api/self-questioning/metrics/{agent}   # Agent metrics
GET  /api/self-questioning/questions/{agent} # Agent questions
POST /api/self-questioning/schedules         # Create schedule
```

---

## 🔄 The 9 Work Type Workflows

### 1. NEW_FEATURE (Spec-Kit Pipeline)
**Agents**: Peter → Felix → Diana  
**Process**: Constitution → Specification → Tasks  
**Output**: Complete project definition with epics/features/stories

### 2. MAINTENANCE (6-Stage Automation)
**Agents**: Marcus → Quinn → Tessa → Eliza  
**Process**: Audit → Plan → Execute → Test → Document → Deploy  
**Output**: Updated dependencies, refactored code, technical debt reduction

### 3. BUG (5-Stage Bug Fixing)
**Agents**: Betty → Tessa → Diana  
**Process**: Reproduce → Diagnose → Fix → Test → Document  
**Output**: Bug fix with regression tests

### 4. QUALITY_AUDIT (SuperClaude Integration)
**Agents**: Quinn → Felix → Marcus  
**Process**: Scan → Analyze → Recommend → Prioritize  
**Output**: Risk-prioritized remediation plan

### 5. ENHANCEMENT
**Agents**: Felix → Tessa → Diana  
**Process**: Design → Implement → Test → Document  
**Output**: Feature enhancement

### 6. MIGRATION (5-Stage Pipeline)
**Agents**: Miguel → Felix → Tessa → Diana  
**Process**: Assess → Plan → Execute → Validate → Cutover  
**Output**: Migrated codebase

### 7. QUALITY_IMPROVEMENT
**Agents**: Quinn → Marcus → Tessa  
**Process**: Audit → Refactor → Test  
**Output**: Improved code quality

### 8. TESTING
**Agents**: Tessa → Quinn → Diana  
**Process**: Strategy → Execute → Report  
**Output**: Comprehensive test suite

### 9. PROJECT_DEFINITION (Complete Project Setup)
**Agents**: Peter → Felix → Paul → Diana  
**Process**: Vision → Architecture → Planning → Documentation  
**Output**: Complete project charter with folder structure

---

## 🎭 Scrum Ceremonies (4 Automated)

### 1. Daily Standup
**Frequency**: On-demand or scheduled  
**Participants**: All active agents  
**Output**: Status reports, blockers, peer assistance requests

### 2. Sprint Planning
**Frequency**: Start of sprint (2 weeks)  
**Process**: Backlog prioritization → Capacity planning → Story selection  
**Output**: Sprint backlog with risk assessment

### 3. Sprint Review
**Frequency**: End of sprint  
**Process**: Demo preparation → Stakeholder feedback → Acceptance validation  
**Output**: Accepted work + backlog refinements

### 4. Sprint Retrospective
**Frequency**: After sprint review  
**Process**: Feedback collection → Team health assessment → Action items  
**Output**: Process improvements + learning outcomes

---

## 🎯 Quality Gates Integration

**7 Gate Types**: Architecture, Code Quality, Test Coverage, Security, Documentation, Performance, Accessibility  
**42 Validation Rules**: Distributed across 5 validators  
**Retry Mechanism**: 3 attempts with exponential backoff  
**Peer Assistance**: Agent-to-agent help (confidence > 0.6)  
**Escalation**: Multi-channel notifications for critical issues

---

## ⚡ The 16 SuperClaude Slash Commands

### Core 4 Commands (Detailed)

#### /architect 🏗️
**Purpose**: Architecture reviews & design pattern recommendations  
**Output**: Architecture score, patterns detected, recommendations  
**Use When**: Architecture changes, design reviews

#### /reviewer 👀
**Purpose**: PR reviews & code quality audits  
**Output**: Quality score, code smells, refactoring suggestions  
**Use When**: Pull request reviews, code quality checks

#### /optimizer ⚡
**Purpose**: Performance audits & bottleneck detection  
**Output**: Performance score, bottlenecks, optimization strategies  
**Use When**: Performance issues, slow queries

#### /debugger 🐛
**Purpose**: Bug investigation & root cause analysis  
**Output**: Robustness score, potential bugs, fix recommendations  
**Use When**: Debugging complex issues, error analysis

### Additional 12 Commands

- **/tester** 🧪 - Test generation & strategy
- **/documenter** 📚 - Documentation generation
- **/security** 🔒 - Security audit (OWASP Top 10)
- **/refactor** 🔄 - Refactoring suggestions
- **/api-designer** 🔌 - API design review
- **/database** 🗄️ - Database optimization
- **/frontend** 🎨 - Frontend review (UI/UX)
- **/backend** ⚙️ - Backend analysis
- **/devops** 🚀 - DevOps review (CI/CD)
- **/accessibility** ♿ - A11y audit (WCAG)
- **/performance** ⚡ - Performance audit
- **/migration** 📦 - Migration strategy

---

## 🔧 LLM Configuration (100% Local)

**All models via Ollama** - No cloud dependencies, complete privacy

| Model | Size | Agents | Specialty |
|-------|------|--------|-----------|
| qwen2.5-coder:7b | 4.7 GB | Felix, Marcus, Tessa, Miguel | Code generation & refactoring |
| deepseek-r1:latest | 5.2 GB | Quinn, Eliza, Peter | Reasoning & analysis |
| codellama:latest | 3.8 GB | Betty | Debugging |
| mistral:latest | 4.4 GB | Diana | Documentation |
| qwen2.5:7b | 4.7 GB | Paul | Planning |

**Benefits**:
- ✅ Complete privacy (no data leaves your machine)
- ✅ No API costs
- ✅ Offline capability
- ✅ Consistent performance

---

## 🔄 Retry + Peer Assistance System

### Retry Mechanism
- **Max Attempts**: 3
- **Backoff**: Exponential (2s → 4s → 8s)
- **Enhanced Feedback**: Quality gate recommendations + slash command insights
- **Blocking Detection**: Automatic escalation after max retries

### Peer Assistance
- **Trigger**: Agent requests help during standup
- **Selection**: Confidence scoring (>0.6 required)
- **Assistance Types**: TIP, RESOURCE, TAKEOVER, PAIR, REVIEW, CONSULT
- **Expertise Mapping**: Each agent has 3-5 specialties

### Human Escalation
- **Channels**: EMAIL, SLACK, WEBHOOK, LOG
- **Priority Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Immediate Escalation**: BUG & QUALITY_AUDIT work types
- **Auto-Resolution**: Self-correcting errors

---

## 📊 Agent Collaboration Patterns

### Sequential Pattern
**Use When**: Each step depends on previous output  
**Example**: NEW_FEATURE (Peter → Felix → Diana)  
**Benefit**: Clear dependencies, ordered execution

### Parallel Pattern
**Use When**: Independent tasks can run simultaneously  
**Example**: QUALITY_AUDIT (multiple code scans)  
**Benefit**: Faster execution

### Hybrid Pattern (Most Common)
**Use When**: Mix of dependent and independent tasks  
**Example**: MAINTENANCE (audit parallel, fixes sequential)  
**Benefit**: Optimal speed + correct dependencies

---

## 🚀 Quick Start

### Run a Workflow

```bash
# Via API
curl -X POST http://localhost:8000/api/workflows/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "work_type": "NEW_FEATURE",
    "description": "Build user authentication system",
    "enable_retry": true,
    "enable_peer_help": true
  }'
```

### Check Agent Status

```bash
curl http://localhost:8000/api/workflows/agents
```

### Get Statistics

```bash
curl http://localhost:8000/api/workflows/statistics
```

---

## 🔍 Troubleshooting

### Agent Not Responding
1. Check Ollama is running: `ollama list`
2. Verify model is pulled: `ollama pull qwen2.5-coder:7b`
3. Check agent service logs

### Workflow Timeout
- Default: 30 minutes (soft timeout with warnings)
- User-controlled execution (no automatic kills)
- Check work type complexity

### Quality Gate Failures
- Review gate configuration in ARCHITECTURE.md
- Check which validation rule failed
- Use slash commands for enhanced feedback

---

## 📚 Related Documentation

- **Full Agent Specifications**: `backend/agents/AGENT_SPECIFICATIONS.md`
- **Integration Guide**: `backend/agents/INTEGRATION_GUIDE.md`  
- **LLM Configuration**: `backend/agents/LLM_CONFIGURATION.md`
- **Architecture Details**: `ARCHITECTURE.md`
- **Planning & Roadmap**: `ROADMAP.md`

---

**Last Updated**: 2025-11-16  
**Version**: 2.0 (Consolidated)  
**Status**: ✅ Complete - All 10 agents operational
