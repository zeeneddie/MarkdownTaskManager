# 🤖 AGENTS - AI Agent System Reference

**Doel**: Complete agent system documentation op één plek
**Doelgroep**: Developers working with agents
**Last Updated**: 2025-12-10 (Week 62 CodeWiki Integration Added)

---

## 🎯 Quick Overview

**3-Layer Agent Architecture** - Scalable multi-stack platform
**10 Core Agents** - Cross-stack expertise (Ollama + Claude routing)
**Stack Agent Templates** - Per-project tech-stack agents
**5 MigrationAnalyzer Agents** - Legacy code analysis (Week 65-70) 📋 PLANNED
**4 Platform Agents** - Meta-level observability & optimization
**11 Work Type Workflows** - Intelligent routing (incl. GREEN_PAPER & BROWN_PAPER)
**Quality Gates** - Integrated validation
**🧬 Self-Evolution** - Continuous improvement via A/B testing
**📚 CodeWiki Integration** - Automated code documentation (Week 62) 📋 PLANNED

---

## 🏗️ 3-Layer Agent Architecture (Week 54+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MARQED AI AGENT PLATFORM                          │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │            LAAG 1: CORE AGENTS (10 - Cross-Stack)             │  │
│  │                                                                │  │
│  │  Felix (Architecture)     Quinn (Quality)      Betty (Bugs)    │  │
│  │  Eliza (Estimation)       Diana (Docs)         Marcus (Maint)  │  │
│  │  Tessa (Testing)          Miguel (Migration)   Peter (PO)      │  │
│  │  Paul (Project Lead)                                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │         LAAG 2: STACK AGENT TEMPLATES (Per Project)           │  │
│  │                                                                │  │
│  │  Python:      BackendDev_py, CodeRev_py, SecAudit_py          │  │
│  │  JavaScript:  BackendDev_js, FrontendDev_js, CodeRev_js       │  │
│  │  Go:          BackendDev_go, CodeRev_go, SecAudit_go          │  │
│  │  Rust:        BackendDev_rs, CodeRev_rs, SecAudit_rs          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │           LAAG 3: PLATFORM AGENTS (Meta-niveau)               │  │
│  │                                                                │  │
│  │  ObservabilityEngineer    - Agent behavior monitoring          │  │
│  │  PromptEngineer           - Meta-prompting, optimization       │  │
│  │  IncidentResponder        - Cross-project incident handling    │  │
│  │  ContextManager           - Cross-agent state management       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              PROVIDER REGISTRY (Multi-LLM Routing)            │  │
│  │                                                                │  │
│  │  Ollama (Local):  qwen2.5-coder, deepseek-r1, codellama       │  │
│  │  Claude CLI:      Haiku (fast), Sonnet (balanced), Opus       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Zie**: [Multi-Stack Platform Architecture](docs/architecture/multi-stack-platform.md)

---

## 📋 Layer 1: Core Agents (10)

Cross-stack expertise - work on any project regardless of tech-stack.

### Development Agents (8)

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

## 🔧 Layer 2: Stack Agent Templates (Week 56-57)

Stack-specific agents instantiated per project via **Stack Agent Factory**.

| Stack | Available Templates | Model Preference |
|-------|---------------------|------------------|
| **Python** | BackendDev_py, CodeRev_py, SecAudit_py, Tester_py | qwen2.5-coder:7b |
| **JavaScript** | BackendDev_js, FrontendDev_js, CodeRev_js, SecAudit_js | qwen2.5-coder:7b |
| **Go** | BackendDev_go, CodeRev_go, SecAudit_go, Tester_go | deepseek-coder |
| **Rust** | BackendDev_rs, CodeRev_rs, SecAudit_rs, Tester_rs | deepseek-coder |

### Template Example

```python
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
    },
}
```

**Status:** PLANNED (Week 56-57)
**Zie**: [Multi-Stack Platform Architecture](docs/architecture/multi-stack-platform.md)

---

## 🔬 Layer 2B: MigrationAnalyzer Agents (Week 65-70) 📋 PLANNED

Gespecialiseerde agents voor legacy code migratie analyse. Multi-agent architectuur voor context efficiency (~65% token savings).

**Specification**: [Migration Analyzer Specification](docs/architecture/migration-analyzer-specification.md)

### Orchestrator

#### Miguel - Migration Orchestrator (Enhanced)
- **Role**: Coordination, stack detection, report aggregation
- **LLM**: deepseek-r1:latest (local)
- **Context**: 2K base + routing overhead
- **Skills**: Stack detection, agent routing, FP totaling, risk aggregation
- **Tools**: tree-sitter (AST), Lizard (complexity), file scanning

### Stack Analyzers (Conditional Activation)

Only activated when relevant stack is detected in target project.

#### DotNetAnalyzerAgent
- **Role**: .NET/C#, WebForms, ASP Classic analysis
- **LLM**: qwen2.5-coder:7b (local)
- **Context**: 4K per component batch
- **Skills**: ASPX parsing, ViewState detection, codebehind analysis, UpdatePanel patterns
- **Tools**: .NET Upgrade Assistant, Roslyn Analyzers, tree-sitter C#
- **Legacy Patterns**: ASPX codebehind, ViewState, ScriptManager, WebForms lifecycle, ASP Classic includes

#### FrontendAnalyzerAgent
- **Role**: Angular, Vue, React, jQuery, AngularJS analysis
- **LLM**: qwen2.5-coder:7b (local)
- **Context**: 4K per component batch
- **Skills**: Framework detection, version identification, component structure analysis
- **Tools**: tree-sitter JS/TS, ESLint legacy plugins, npm-check-updates
- **Legacy Patterns**: AngularJS $scope, Vue Options API, React class components, jQuery DOM manipulation

#### PHPAnalyzerAgent
- **Role**: PHP 5.x-8.x, Laravel, Symfony analysis
- **LLM**: qwen2.5-coder:7b (local)
- **Context**: 4K per component batch
- **Skills**: PHP version detection, framework identification, deprecated function detection
- **Tools**: PHP_CodeSniffer, PHPStan, tree-sitter PHP
- **Legacy Patterns**: mysql_* functions, register_globals, magic quotes, PHP4 class syntax

#### JavaAnalyzerAgent (Optional)
- **Role**: Java/J2EE, Spring, Struts analysis
- **LLM**: qwen2.5-coder:7b (local)
- **Context**: 4K per component batch
- **Skills**: Java version detection, framework identification, servlet analysis
- **Tools**: PMD, SpotBugs, tree-sitter Java
- **Legacy Patterns**: Struts 1.x, EJB 2.x, JSP scriptlets, Servlet 2.x

### Database Analyzer

#### DatabaseAnalyzerAgent
- **Role**: Schema analysis, version detection, conversion assessment
- **LLM**: qwen2.5-coder:7b (local)
- **Context**: 3K + schema definitions
- **Skills**: Schema parsing, version detection, compatibility analysis
- **Tools**: Ora2Pg, SQLines, pgLoader, schema-diff
- **Database Support**:
  - SQL Server → PostgreSQL
  - Oracle → PostgreSQL
  - MySQL → PostgreSQL
- **Difficulty Rating**: A-E scale (Easy → Impossible)

### Cross-Cutting Agents (Extended for Migration)

| Agent | Migration Role | Additional Skills |
|-------|----------------|-------------------|
| **Quinn** | Security legacy patterns | OWASP legacy detection, SQL injection in ASP/PHP |
| **Eliza** | Migration FP estimation | Legacy complexity multiplier, DB conversion effort |
| **Felix** | Target architecture | Clean Architecture recommendations, strangler fig |
| **Diana** | Report generation | Migration plan documentation, risk reports |
| **Peter** | BMAD auto-fill | Populate 8 questions from analysis results |

### Token Efficiency

| Approach | Tokens per Analysis | Savings |
|----------|---------------------|---------|
| Mega-agent | ~35K | Baseline |
| Multi-agent | ~12K | **65% savings** |

**Conditional Activation Example**:
```python
# Only .NET detected → Only DotNetAnalyzer loaded
# Frontend detected → FrontendAnalyzer loaded
# Both detected → Both loaded
# No PHP → PHPAnalyzer never instantiated
```

---

## 📚 CodeWiki Integration (Week 62) 📋 PLANNED

**Bron:** github.com/zeeneddie/CodeWiki
**Doel:** Automated repository documentation generation voor pre-analysis en agent context enrichment

### Wat is CodeWiki?

AI-powered tool dat complete codebases analyseert en gestructureerde documentatie genereert:

| Feature | Beschrijving |
|---------|--------------|
| **Multi-Language** | Python, Java, JavaScript, TypeScript, C, C++, C# |
| **Architecture Diagrams** | Mermaid diagrammen (module relaties, data flow, sequence) |
| **Module Mapping** | Hiërarchische decompositie (module_tree.json) |
| **Output Formats** | Markdown, JSON, HTML (GitHub Pages compatible) |
| **Accuracy** | 79% voor high-level languages (Python, JS, TS) |

### CodeWiki → Agent Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CODEWIKI AGENT INTEGRATION                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Repository → CodeWiki → module_tree.json + diagrams + docs        │
│                              ↓                                      │
│         ┌────────────────────┼────────────────────┐                │
│         ↓                    ↓                    ↓                │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│  │   Miguel    │     │   Felix     │     │   Quinn     │          │
│  │ (Migration) │     │ (Architect) │     │ (Quality)   │          │
│  │             │     │             │     │             │          │
│  │ Structured  │     │ Architecture│     │ Module deps │          │
│  │ "as-is"     │     │ diagrams    │     │ for impact  │          │
│  │ analysis    │     │ for design  │     │ analysis    │          │
│  └─────────────┘     └─────────────┘     └─────────────┘          │
│         │                    │                    │                │
│         └────────────────────┼────────────────────┘                │
│                              ↓                                      │
│                    ┌─────────────┐                                 │
│                    │   Diana     │                                 │
│                    │   (Docs)    │                                 │
│                    │             │                                 │
│                    │ Generated   │                                 │
│                    │ docs as     │                                 │
│                    │ template    │                                 │
│                    └─────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Enhancements via CodeWiki

| Agent | CodeWiki Input | Enhancement |
|-------|----------------|-------------|
| **Miguel** | module_tree.json + diagrams | Pre-analyzed "as-is" architecture voor migration analysis |
| **Felix** | Architecture diagrams | Visual input voor design decisions, pattern recognition |
| **Quinn** | Module dependencies | Accurate impact analysis bij code changes |
| **Diana** | Generated documentation | Template basis, consistent documentation style |
| **Betty** | Data flow diagrams | Root cause analysis, error propagation tracing |
| **Peter** | Module overview | Auto-fill BMAD technical questions |

### Use Cases

1. **MigrationAnalyzer Pre-Analysis (Week 65+)**
   - CodeWiki scant legacy codebase vóór Miguel start
   - Miguel ontvangt structured data ipv raw code
   - ~30% snellere analyse, hogere accuracy

2. **Brown Paper Workflow Enhancement**
   - Auto-fill "Legacy System Analysis" (BMAD vraag 1)
   - Architecture diagrams voor "Migration Target" planning
   - Reduce manual technical discovery effort

3. **Project Onboarding**
   - Instant README-quality docs bij project registration
   - LLM Council krijgt rijke context voor onboarding docs
   - Snellere developer onboarding

4. **Agent Context Enrichment**
   - Alle agents krijgen gestructureerde code understanding
   - Minder tokens nodig voor raw code context
   - Betere beslissingen door visuele architectuur info

### API Endpoints (6)

```
POST /api/codewiki/analyze/{project_id}     - Start repository analyse
GET  /api/codewiki/{project_id}/modules     - Get module tree (JSON)
GET  /api/codewiki/{project_id}/diagram     - Get architecture diagram (Mermaid)
GET  /api/codewiki/{project_id}/docs        - Get generated documentation
GET  /api/codewiki/{project_id}/status      - Check analyse status
POST /api/codewiki/{project_id}/refresh     - Re-analyse repository
```

### ChromaDB Integration

CodeWiki output wordt geïndexeerd in ChromaDB voor semantic search:

```python
CODEWIKI_COLLECTIONS = {
    "codewiki_modules": "Module descriptions + relationships",
    "codewiki_diagrams": "Architecture diagram metadata",
    "codewiki_docs": "Generated documentation chunks",
}
```

**Status:** PLANNED (Week 62)
**Effort:** 16 uur
**Dependencies:** Node.js (Mermaid), LLM API access
**Zie:** [ROADMAP.md Week 62](ROADMAP.md#week-62-code-understanding-week---codewiki--deepcode--archon-48-uur)

---

## 🔍 Layer 3: Platform Agents (Week 54-55) 🚧 IN PROGRESS

Meta-level agents that monitor, optimize, and coordinate the entire platform.

### ObservabilityEngineer ✅ IMPLEMENTED
- **Role**: Agent behavior monitoring
- **Capabilities**: Action logging, decision tracing, performance metrics
- **Output**: Real-time dashboards, pattern detection
- **Implementation**:
  - `app/services/observability_service.py` - Core service
  - `app/api/observability.py` - 12 API endpoints
  - `frontend/observability-dashboard.html` - Live dashboard

### PromptEngineer
- **Role**: Meta-prompting & continuous improvement
- **Capabilities**: Prompt A/B testing, automatic optimization, pattern learning
- **Output**: Enhanced prompts, improvement recommendations
- **Status**: PLANNED (Week 56-57)

### IncidentResponder
- **Role**: Cross-project incident handling
- **Capabilities**: Distributed debugging, cascading failure analysis, log aggregation
- **Output**: Root cause analysis, remediation plans
- **Status**: PLANNED (Week 56-57)

### ContextManager
- **Role**: Cross-agent state management
- **Capabilities**: Context sharing, handoff coordination, state persistence
- **Output**: Seamless agent collaboration
- **Status**: PLANNED (Week 56-57)

**Status:** Week 54-55 IN PROGRESS (ObservabilityEngineer done, others planned)
**Zie**: [Multi-Stack Platform Architecture](docs/architecture/multi-stack-platform.md)

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

## 🎯 Agent OS Integratie (Week 59-60 PLANNED)

**Bron**: github.com/zeeneddie/agent-os
**Status**: Kwalitatieve analyse COMPLETE, implementatie PLANNED

### Nieuwe Capabilities vanuit Agent OS

8 unieke concepten die worden toegevoegd aan het MarQed platform:

| # | Concept | Agent Impact | Bron |
|---|---------|--------------|------|
| 1 | **Standards context loading** | Alle agents | .standards/ folder |
| 2 | **Visuele asset validatie** | Quinn | verify-spec |
| 3 | **Reusability check** | Felix, Quinn | verify-spec |
| 4 | **Verplichte visuals folder** | Peter, Felix | research-spec |
| 5 | **Strikte scope beperking** | Alle agents | implement-tasks |
| 6 | **Skill description rewriting** | Alle agents | improve-skills |
| 7 | **Spec iteration loop** | Felix | spec-shaper |
| 8 | **Quick Spec templates** | Peter, Felix | patterns |

### Nieuwe Capabilities per Agent

| Agent | Nieuwe Capability | Beschrijving |
|-------|-------------------|--------------|
| **Felix** | Standards context loading | Laadt relevante .standards/ voor workflow |
| **Felix** | Spec iteration loop | Shape → Verify → Loop tot spec voldoet |
| **Felix** | Reusability check | Identificeer herbruikbare componenten |
| **Quinn** | Visual asset validation | Check dat designs/mockups bestaan |
| **Quinn** | Reusability check | Tech debt preventie via spec verificatie |
| **Diana** | Standards documentation | Documenteert coding standards |
| **Peter** | Verplichte visuals folder | Design-first spec aanpak |
| **All** | Strikte scope beperking | Expliciete instructie: ALLEEN toegewezen taken |
| **All** | Skill description rewriting | Betere agent discoverability |

### /improve-skills Command (NIEUW)

```bash
/improve-skills [agent] --focus=[area] --workflow=[type]

# Voorbeelden:
/improve-skills felix --focus=architecture
/improve-skills betty --focus=debugging --workflow=BUG
/improve-skills quinn --focus=security --workflow=QUALITY_AUDIT
```

**Integratie met bestaande Self-Questioning**:
- Roept SelfQuestioningEngine aan met focus parameter
- Schrijft skill descriptions voor betere discoverability
- Logt learning naar ChromaDB experience store

### Standards System (.standards/)

```
.standards/
├── global/                    # Altijd geladen voor alle workflows
│   ├── git-conventions.md
│   ├── code-review.md
│   └── naming-conventions.md
├── backend/                   # Geladen bij backend werk
│   ├── python-fastapi.md
│   └── sqlalchemy.md
├── frontend/                  # Geladen bij frontend werk
│   └── html-accessibility.md
├── testing/                   # Geladen bij test-gerelateerd werk
│   └── unit-test-patterns.md
└── security/                  # Geladen bij security-gerelateerd werk
    └── owasp-top-10.md
```

### Workflow → Standards Mapping

| Workflow | Standards Auto-Loaded |
|----------|----------------------|
| GREEN_PAPER | global/ |
| BROWN_PAPER | global/, backend/, frontend/, security/ |
| MAINTENANCE | global/, backend/, testing/ |
| BUG | global/, testing/ |
| NEW_FEATURE | global/, backend/, frontend/, testing/ |
| QUALITY_AUDIT | global/, security/, testing/ |

### Kwalitatieve Vergelijking: Agent OS vs MarQed

| Aspect | Agent OS | MarQed | Conclusie |
|--------|----------|--------|-----------|
| Visual-first | ✅ Sterk | ❌ Gap | Toevoegen |
| Standards | ✅ Files | ❌ Gap | Toevoegen |
| Spec iteration | ✅ Loop | ❌ One-shot | Toevoegen |
| Multi-LLM | ❌ Claude only | ✅ 3 providers | **MarQed beter** |
| Learning | ❌ Geen | ✅ ChromaDB | **MarQed beter** |
| Validation | 7 checks | 42 rules | **MarQed beter** |

**Details**: [ROADMAP.md](ROADMAP.md#week-59-60-agent-os-integratie-8-concepten)

---

## 🔍 Enhanced Observability (CCTrace Integration) - Week 61 PLANNED

**Bronnen**: github.com/jimmc414/cctrace + github.com/alexfazio/cc-trace
**Status**: Analyse COMPLETE, implementatie PLANNED
**Doel**: Deep agent behavior analysis via Thinking Blocks + Complete Tool I/O + Session Export

### Per-Agent Observability Features

Alle agents krijgen dezelfde enhanced observability capabilities:

| Agent | Thinking Capture | Tool I/O | Export | Impact |
|-------|-----------------|----------|--------|--------|
| **Alle Core Agents** | ✅ | ✅ | ✅ | Debugging, learning |
| **Stack Templates** | ✅ | ✅ | ✅ | Per-project analyse |
| **Platform Agents** | ✅ | ✅ | ✅ | Meta-observability |

### Multi-Provider Thinking Capture

| Provider | Method | Beschrijving |
|----------|--------|--------------|
| Claude CLI | Native `thinking` blocks | Direct extraheren uit API response |
| Codex CLI | Pseudo-thinking wrapper | Reasoning triggeren en extraheren |
| Ollama | CoT forcing | `<thinking>` tags via prompt template |

**Ollama CoT Forcing Template**:
```
Before answering, think through the problem step by step.
Format your thinking in <thinking>...</thinking> tags.
Then provide your final answer.
```

### Self-Evolution Integration

Thinking blocks voeden direct de Self-Evolution pipeline:

| Integration Point | Input | Learning Output |
|-------------------|-------|-----------------|
| **ChromaDB** | Thinking patterns | `thinking_patterns` collection |
| **Self-Questioning** | "Welke redenering leidde tot succes?" | Edge case identification |
| **Decision Attribution** | Tool usage patterns | "Welke tools waren effectief?" |
| **A/B Testing** | Thinking comparison | Compare reasoning between variants |

### Nieuwe Database Models

- `ThinkingBlock` - LLM reasoning capture per provider
- `ToolExecution` - Complete tool I/O (geen truncatie)
- `MessageRelationship` - Parent-child conversation threading
- Extended `AgentAction` met token_cache_creation, token_cache_read

### API Endpoints (6 nieuw)

```
GET  /api/observability/thinking/{session_id}       # Thinking blocks per session
GET  /api/observability/thinking/patterns/{agent}   # Thinking patterns per agent
GET  /api/observability/tools/{action_id}           # Full tool I/O
GET  /api/observability/tools/stats/{agent}         # Tool usage statistics
POST /api/observability/export/{session_id}         # Export session (MD/JSON/XML)
GET  /api/observability/messages/{session_id}/tree  # Message tree
```

### Session Export Formats

| Format | Use Case | Voorbeeld |
|--------|----------|-----------|
| **Markdown** | Human-readable documentatie | Retrospectives, reviews |
| **JSON** | Structured analyse | Data pipelines, ML training |
| **XML** | Enterprise compatibility | Integration met andere tools |

**Details**: [ROADMAP.md](ROADMAP.md#week-61-enhanced-observability-cctrace-integration--cost-management)

---

## 🔄 The 11 Work Type Workflows

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

### 10. GREEN_PAPER (Greenfield Project Definition - BMAD 6 Questions) ✨ NEW
**Agents**: Peter → Felix → Diana
**Process**: 6 Strategic Questions → Specification → Tasks
**Output**: Complete constitution for new/greenfield projects
**Questions**:
1. Problem Statement - What problem are we solving?
2. Users & Stakeholders - Who will use this?
3. Solution Vision - What does success look like?
4. Core Features - What must it do?
5. Constraints - What limitations exist?
6. Success Criteria - How do we measure success?

### 11. BROWN_PAPER (Brownfield/Migration Project Definition - BMAD 8 Questions) ✨ NEW
**Agents**: Miguel → Peter → Felix → Diana
**Process**: 8 Strategic Questions → Migration Analysis → Specification → Tasks
**Output**: Complete constitution for brownfield/migration projects

**The 8 Strategic Questions**:
1. **Legacy System Analysis** (Miguel) - Describe the current system, tech stack, pain points
2. **Migration Target** (Miguel) - What is the desired end state?
3. **Migration Strategy** (Miguel) - Strangler Fig, Big Bang, Parallel Run?
4. **Data Migration Approach** (Miguel) - How will data be migrated?
5. **Problem Statement** (Peter) - What problems does this migration solve?
6. **Stakeholders** (Peter) - Who is affected by this migration?
7. **Success Criteria** (Peter) - How do we measure success?
8. **Timeline & Constraints** (Felix) - What are the limitations?

**Pipeline**:
```
Questions → Miguel (Analysis) → Peter (Specification) → Felix (Tasks)
     ↓              ↓                    ↓                   ↓
  8 Answers   Complexity +       Mission/Vision +      Epics/Features/
              Risk Register      Requirements          Stories + FP
```

**API Endpoints**:
```
POST /api/brown-paper/bmad/start              - Start session
GET  /api/brown-paper/bmad/{id}/question      - Get current question
POST /api/brown-paper/bmad/{id}/answer        - Submit answer
POST /api/brown-paper/bmad/{id}/analyze       - Run migration analysis
POST /api/brown-paper/bmad/{id}/specification - Generate specification
POST /api/brown-paper/bmad/{id}/tasks         - Generate task hierarchy
GET  /api/brown-paper/bmad/{id}/export        - Export to markdown
```

**Use When**: Migrating legacy systems, tech stack upgrades, platform modernization

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

## 🔧 LLM Configuration (Multi-Provider)

### Provider Registry (Week 54+)

| Model | Tier | Cost (Input/Output) | Use Case |
|-------|------|---------------------|----------|
| Ollama (local) | Free | $0 / $0 | Simple tasks, privacy, offline |
| Claude Haiku | Fast | $1 / $5 per M | Quick fixes, bulk generation |
| Claude Sonnet | Balanced | $3 / $15 per M | Daily work, most tasks |
| Claude Opus | Deep | $15 / $75 per M | Architecture, security, complex |

### Task-to-Model Routing

```python
TASK_ROUTING = {
    "simple_generation": "ollama/qwen2.5-coder:7b",
    "quick_fix": "claude/haiku",
    "code_review": "claude/sonnet",
    "standard_work": "claude/sonnet",
    "architecture": "claude/opus",
    "security_audit": "claude/opus",
    "complex_analysis": "claude/opus",
}
```

### Local Models (Ollama - Current)

| Model | Size | Agents | Specialty |
|-------|------|--------|-----------|
| qwen2.5-coder:7b | 4.7 GB | Felix, Marcus, Tessa, Miguel | Code generation & refactoring |
| deepseek-r1:latest | 5.2 GB | Quinn, Eliza, Peter | Reasoning & analysis |
| codellama:latest | 3.8 GB | Betty | Debugging |
| mistral:latest | 4.4 GB | Diana | Documentation |
| qwen2.5:7b | 4.7 GB | Paul | Planning |

**Benefits**:
- ✅ Complete privacy (no data leaves your machine)
- ✅ Cost control (local = free)
- ✅ Offline capability
- ✅ Smart routing (complexity → optimal model)

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

### Architecture Documentation
- **Main Overview**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Self-Evolution**: [docs/architecture/self-evolution.md](docs/architecture/self-evolution.md)
- **Project Profiles**: [docs/architecture/project-profiles.md](docs/architecture/project-profiles.md)
- **Validation Framework**: [docs/architecture/validation-framework.md](docs/architecture/validation-framework.md)
- **Quality Gates**: [docs/architecture/quality-gates.md](docs/architecture/quality-gates.md)
- **A/B Testing**: [docs/architecture/ab-testing.md](docs/architecture/ab-testing.md)
- **LLM Council**: [docs/architecture/llm-council.md](docs/architecture/llm-council.md)
- **Continuous Evolution**: [docs/architecture/continuous-evolution.md](docs/architecture/continuous-evolution.md)
- **Multi-Stack Platform**: [docs/architecture/multi-stack-platform.md](docs/architecture/multi-stack-platform.md)

### Agent Implementation
- **Full Agent Specifications**: `backend/agents/AGENT_SPECIFICATIONS.md`
- **Integration Guide**: `backend/agents/INTEGRATION_GUIDE.md`
- **LLM Configuration**: `backend/agents/LLM_CONFIGURATION.md`

### Planning
- **Roadmap**: [ROADMAP.md](ROADMAP.md)
- **Project Status**: [PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md)

---

**Last Updated**: 2025-11-26
**Version**: 3.0 (3-Layer Architecture)
**Status**: ✅ Complete - 10 Core Agents + Platform Agents Planned
