# Upcoming Phases & Platform Overview

**Project:** MarQed AI Agent Software Platform
**Last Updated:** Week 158 (2026-01-15)
**Document Purpose:** Comprehensive roadmap, service inventory, and integration analysis

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Roadmap Timeline](#roadmap-timeline)
3. [Phase Details](#phase-details)
4. [Topic Clusters](#topic-clusters)
5. [Implemented Services by Category](#implemented-services-by-category)
6. [Workflow Integration Matrix](#workflow-integration-matrix)
7. [Services NOT Yet Integrated](#services-not-yet-integrated)
8. [Cleanup Recommendations](#cleanup-recommendations)
9. [Appendix: Agent Roles](#appendix-agent-roles)

---

## Executive Summary

### Current Status

| Metric | Value |
|--------|-------|
| **Total Services** | 221 |
| **Actively Used** | ~180 (81%) |
| **Orphaned/Deprecated** | ~40 (19%) |
| **Phases Completed** | 21+ |
| **Phases Remaining** | 10+ |
| **Estimated Remaining Effort** | ~2,292 hours |
| **Timeline** | Week 158-254 (~96 weeks) |

### Fase 24 Quick Wins Progress

```
Progress: ████████████████████░░░░░░░░░░ 60% (9/15 items)

Completed (9):
✅ A1 - Legacy Quickscan (15-min assessment)
✅ K3 - Secret Detection (50+ patterns)
✅ D1 - Migration Pattern Library (25 patterns)
✅ D2 - Database-First Pattern (55 tests)
✅ K1 - OWASP Integration (30+ patterns)
✅ K2 - CVE Database Integration (NVD/OSV)
✅ A4 - Risk Heat Map (D3.js format)
✅ E1 - Visual Dependency Graph (multi-format)
✅ J1 - Context-Aware Documentation (AST parsing)

Remaining (6):
⏳ B12 - LLM Agent Collaboration
⏳ I1 - API Endpoint Discovery
⏳ F3 - SQL Analysis (Basic)
⏳ M1 - Export Multi-Format
⏳ A3 - Technology Radar
⏳ A5 - Complexity Dashboard
```

---

## Roadmap Timeline

### Visual Timeline (Week 158-254)

```
WEEK    158   165   175   185   195   205   215   225   235   245   254
         │     │     │     │     │     │     │     │     │     │     │
         ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼

    ┌─────────────────────────────┐
    │      FASE 24 (9/15 done)    │ Quick Wins & Foundation
    │      🔄 IN PROGRESS         │ B12, I1, F3, M1, A3, A5
    │      Week 157-174           │
    └──────────────┬──────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│   FASE 32       │  │   FASE 33       │
│ Ralph Wiggum    │  │ DevStats        │
│ Week 175-180    │  │ Week 179-184    │
│ 160h / 5 weken  │  │ 152h / 5 weken  │
│ ROI: 8.5 HIGH   │  │ ROI: 7.0 MED-HI │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └─────────┬──────────┘
                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            FASE 25                                       │
│                  Core Platform Enhancement (18 items)                    │
│                         Week 185-200 (~400h)                             │
│  COBOL Analyzer, UI Wrapper, Knowledge Graph, Persistence Layer          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            FASE 26                                       │
│                    AI & Automation (12 items)                            │
│                         Week 201-214 (~350h)                             │
│  LLM Collaboration Framework, Natural Language Query, Auto-migration     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────────┐               ┌─────────────────────────────┐
│         FASE 27             │               │         FASE 28             │
│   Testing Excellence (8)    │               │  Advanced Integrations (10) │
│      Week 215-224           │               │      Week 225-236           │
│ Characterization, Mutation  │               │ Jira, GitLab, ServiceNow    │
└──────────────┬──────────────┘               └──────────────┬──────────────┘
               │                                             │
               └───────────────────┬─────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FASE GAP-29                                     │
│                   Innovation & Scale (9 items)                           │
│                         Week 237-254 (~350h)                             │
│  Multi-language Translation, Microservices Decomposition, Performance    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────┐
                       │        FASE 30          │
                       │  LLM Council Improve.   │
                       │     Week 233-235        │
                       │ Streaming, Timeouts     │
                       └─────────────────────────┘
```

### Effort Summary Table

| Phase | Title | Hours | Weeks | ROI | Status |
|-------|-------|-------|-------|-----|--------|
| **24** | Quick Wins (remaining) | ~120 | 6 | Various | 🔄 IN PROGRESS |
| **32** | Ralph Wiggum Loop | 160 | 5 | 8.5 | 🆕 PLANNED |
| **33** | DevStats Dashboard | 152 | 5 | 7.0 | 🆕 PLANNED |
| **25** | Core Enhancement | ~400 | 16 | - | PLANNED |
| **26** | AI & Automation | ~350 | 14 | - | PLANNED |
| **27** | Testing Excellence | ~240 | 10 | - | PLANNED |
| **28** | Advanced Integrations | ~300 | 12 | - | PLANNED |
| **GAP-29** | Innovation & Scale | ~350 | 16 | - | PLANNED |
| **30** | LLM Council | 72 | 2 | - | PLANNED |
| **TOTAL** | | **~2,144h** | **~86 wk** | | |

---

## Phase Details

### Fase 24 - Remaining Items (6/15)

| Item | ROI | Title | Topics | Estimated Hours |
|------|-----|-------|--------|-----------------|
| **B12** | 5.0 | LLM Agent Collaboration | AI, Multi-agent, Orchestration | 24h |
| **I1** | 4.5 | API Endpoint Discovery | REST, SOAP, OpenAPI | 20h |
| **F3** | 4.0 | SQL Analysis (Basic) | Database, Query, Performance | 20h |
| **M1** | 4.0 | Export Multi-Format | CSV, Excel, ODS, MS Project | 24h |
| **A3** | 3.7 | Technology Radar | EOL tracking, Risk | 16h |
| **A5** | 3.5 | Complexity Dashboard | Metrics, D3.js | 16h |

### Fase 32 - Ralph Wiggum Autonomous Loop

**Priority:** HIGH (ROI 8.5)
**Effort:** 160 hours / 5 weeks

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THREE-LAYER ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LAYER 1: PRP FRAMEWORK                                                  │
│  ───────────────────────                                                 │
│  Research → Requirements → Blueprint → Engineered PROMPT                 │
│                                                                          │
│  LAYER 2: RALPH LOOP                                                     │
│  ───────────────────────                                                 │
│  while (!complete && iterations < max) {                                 │
│      inject(guardrails + progress)                                       │
│      result = execute(PROMPT)                                            │
│      commit(changes) → validate() → evaluate(completion)                 │
│  }                                                                       │
│                                                                          │
│  LAYER 3: PRODUCTION HARNESS (Cole Medin)                                │
│  ─────────────────────────────────────────                               │
│  • InitializationAgent - Context gathering before work                   │
│  • StructuredProgressTracker - Rich metrics beyond files                 │
│  • StageApprovalWorkflow - Human approval between stages                 │
│  • RollbackService - Git reset + regression testing                      │
│  • MemoryCompressionService - Context handoff between runs               │
│  • MultiPhaseValidationPipeline - 8-phase validation                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Components:**
| Component | Purpose |
|-----------|---------|
| RalphLoopService | Core autonomous execution loop |
| GuardrailsService | File-based cross-context learning |
| CourseCorrectionService | Dead-end detection, 5 Whys methodology |
| CompletionDetector | Dual-gate exit logic |
| CircuitBreaker | Stuck detection, cost limits |

### Fase 33 - DevStats Developer Metrics

**Priority:** MEDIUM-HIGH (ROI 7.0)
**Effort:** 152 hours / 5 weeks

```
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ CONTRIBUTION  │ │  BUS FACTOR   │ │   RELEASE     │ │  CODE CHURN   │
│    METRICS    │ │   ANALYSIS    │ │ CORRELATION   │ │   TRACKING    │
├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────────┤
│• Commits/week │ │• Min devs     │ │• % per release│ │• Lines +/-    │
│• Lines changed│ │• Ownership %  │ │• Velocity     │ │• Rework rate  │
│• Files touched│ │• Knowledge    │ │• Lead time    │ │• Dead code    │
│• Time patterns│ │  silos        │ │• Hotfix ratio │ │• Complexity   │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                         │
              ┌──────────┴──────────┐
              │   PR CYCLE METRICS  │
              ├─────────────────────┤
              │ • Open duration     │
              │ • Review turnaround │
              │ • Comments per PR   │
              │ • Approval rate     │
              └─────────────────────┘
```

**Key Components:**
| Component | Purpose |
|-----------|---------|
| GitDataCollector | GitHub/GitLab/Bitbucket API integration |
| IdentityMerger | Multi-identity developer resolution |
| BusFactorCalculator | Knowledge concentration risk |
| ReleaseCorrelator | Contribution-to-release mapping |
| D3Visualizations | Heatmaps, treemaps, timelines, funnels |

---

## Topic Clusters

### Domain Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOPIC CLUSTERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐        │
│  │     🤖 AI & AGENTS          │     │     🔒 SECURITY             │        │
│  │     ─────────────────       │     │     ─────────────────       │        │
│  │  Fase 32: Ralph Wiggum      │     │  Fase 31: CWE Scanners ✅    │        │
│  │  Fase 24-B12: LLM Collab    │     │  Fase 24-K1: OWASP ✅        │        │
│  │  Fase 26: AI Automation     │     │  Fase 24-K2: CVE DB ✅       │        │
│  │  Fase 30: LLM Council       │     │  Fase 24-K3: Secrets ✅      │        │
│  └─────────────────────────────┘     └─────────────────────────────┘        │
│                                                                              │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐        │
│  │     📊 VISUALIZATIONS       │     │     📈 ANALYTICS            │        │
│  │     ─────────────────       │     │     ─────────────────       │        │
│  │  Fase 24-A4: Heat Map ✅     │     │  Fase 33: DevStats          │        │
│  │  Fase 24-E1: Dep Graph ✅    │     │  Fase 24-A5: Complexity     │        │
│  │  Fase 24-A3: Tech Radar     │     │  Fase 29: Quality Impact ✅  │        │
│  │  D3.js / Cytoscape / DOT    │     │  Bus Factor Analysis        │        │
│  └─────────────────────────────┘     └─────────────────────────────┘        │
│                                                                              │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐        │
│  │     🔄 MIGRATION            │     │     🧪 TESTING              │        │
│  │     ─────────────────       │     │     ─────────────────       │        │
│  │  Fase 24-D1: Patterns ✅     │     │  Fase 27: Excellence        │        │
│  │  Fase 24-D2: DB-First ✅     │     │  Characterization Tests     │        │
│  │  Fase 24-A1: Quickscan ✅    │     │  Mutation Testing           │        │
│  │  Strangler Fig Pattern      │     │  Golden Master Pattern      │        │
│  └─────────────────────────────┘     └─────────────────────────────┘        │
│                                                                              │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐        │
│  │     🔗 INTEGRATIONS         │     │     📝 DOCUMENTATION        │        │
│  │     ─────────────────       │     │     ─────────────────       │        │
│  │  Fase 28: Jira/GitLab       │     │  Fase 24-J1: Context ✅      │        │
│  │  Fase 28: ServiceNow        │     │  Fase 24-I1: API Discovery  │        │
│  │  Fase 24-M1: Multi-Export   │     │  AST Parsing                │        │
│  │  GitHub/Azure DevOps ✅      │     │  Multi-format Export        │        │
│  └─────────────────────────────┘     └─────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cross-Phase Dependencies

```
                         ┌────────────────────┐
                         │  FASE 24 (Current) │
                         │   Quick Wins 9/15  │
                         └─────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
     ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
     │   FASE 32      │   │   FASE 33      │   │   FASE 25      │
     │ Ralph Wiggum   │   │   DevStats     │   │ Core Platform  │
     │  (AI Agents)   │   │  (Analytics)   │   │  (Foundation)  │
     └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │      FASE 26       │
                         │  AI & Automation   │
                         │ (LLM + ML Features)│
                         └─────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
           ┌────────────────┐            ┌────────────────┐
           │    FASE 27     │            │    FASE 28     │
           │    Testing     │            │  Integrations  │
           └───────┬────────┘            └───────┬────────┘
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │    FASE GAP-29     │
                         │ Innovation & Scale │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │     FASE 30        │
                         │  LLM Council 2.0   │
                         └────────────────────┘
```

---

## Implemented Services by Category

### 1. Security (7 services) ✅ WELL-INTEGRATED

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `CyberStrikeService` | ✅ Active | Brown Paper, Quality | OWASP Top 10, Bandit, Safety, Semgrep |
| `SecurityRagService` | ✅ Active | All workflows | OWASP/CWE knowledge base with RAG |
| `SecurityWorkflowService` | ✅ Active | Orchestrator | Security scanning coordination |
| `GhostCrewService` | ⚠️ Review | Autonomous mode | May overlap with CyberStrike |
| `SecurityPatternLoader` | ✅ Active | All scanners | YAML pattern loading |
| `MigrationSecurityService` | ✅ Active | Quinn agent | Legacy OWASP patterns |
| `RiskHeatMapService` | ❌ Orphaned | None | **Needs API route** |

### 2. Code Analysis (12 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `CodeAnalysisAggregatorService` | ✅ Active | Brown Paper | Unified static analysis |
| `DependencyGraphService` | ✅ Active | All workflows | Multi-format export |
| `VisualDependencyGraphService` | ❌ Orphaned | None | **Needs API route** |
| `DeadCodeDetectorService` | ✅ Active | Quality | Multi-language support |
| `CodeCoverageAnalyzerService` | ✅ Active | Quality, Tessa | Coverage analysis |
| `StackDetectionService` | ✅ Active | Brown Paper | 20+ tech stacks |
| `KnowledgeGraphService` | ✅ Active | Felix agent | Entity relationships |
| `CodeTransformationService` | ✅ Active | Migration | VB→C#, T-SQL→PL/pgSQL |
| `CodeWikiService` | ✅ Active | Documentation | Structure analysis |
| `DatabaseAnalyzerService` | ✅ Active | Migration | Schema analysis |
| `TechnicalDebtService` | ✅ Active | Marcus agent | TDR, interest, ROI |
| `Ora2pgWrapperService` | ⚠️ Review | Migration | Overlaps with CodeTransformation |

### 3. Migration (12 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `StranglerFigService` | ✅ Active | Migration | Incremental pattern |
| `MigrationAnalyzerService` | ✅ Active | Migration | Legacy analysis |
| `MigrationEstimationService` | ✅ Active | Eliza agent | IFPUG FP methodology |
| `MigrationPlanningOrchestrator` | ✅ Active | Orchestrator | Workflow coordination |
| `MigrationEnhancedService` | ⚠️ Review | Migration | May duplicate base |
| `MigrationReportService` | ✅ Active | Diana agent | Report generation |
| `MigrationArchitectureService` | ✅ Active | Felix agent | Target architecture |
| `DatabaseMigrationExecutorService` | ✅ Active | Migration | Schema/data migration |
| `DatabaseFirstMigrationService` | ⚠️ Partial | None | **Needs API route** |
| `AsisArchitectureService` | ✅ Active | Brown Paper | AS-IS analysis |
| `ApiInventoryService` | ✅ Active | Migration | API cataloging |
| `SqlinesWrapperService` | ⚠️ Review | Migration | Overlaps with CodeTransformation |

### 4. Visualization (12 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `VisualDependencyGraphService` | ❌ Orphaned | None | **Needs API route** |
| `DependencyGraphService` | ✅ Active | All | Mermaid/DOT/JSON/D3 |
| `RiskHeatMapService` | ❌ Orphaned | None | **Needs API route** |
| `CodechartaExporterService` | ✅ Active | Reports | 3D city metaphor |
| `ErdGeneratorService` | ✅ Active | Migration | Mermaid/PlantUML |
| `GraphPersistenceService` | ✅ Active | Storage | Graph storage |
| `GraphWorkflowService` | ✅ Active | Orchestrator | Graph workflows |
| `GraphWorkflowIntegrationService` | ✅ Active | Orchestrator | Integration wrapper |
| `JourneyAnalyticsService` | ✅ Active | Analytics | Journey visualization |
| `TrendAnalysisService` | ✅ Active | Dashboard | Trend tracking |
| `EvolutionDashboardService` | ✅ Active | Dashboard | Agent metrics |
| `ShadowGraphService` | ✅ Active | Analysis | Conflict analysis |

### 5. Documentation (12 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `DocumentationTemplates` | ✅ Active | All | Standard templates |
| `DeepExtractionService` | ✅ Active | Brown Paper | 6-cycle hybrid |
| `ContextAwareDocumentationService` | ❌ Orphaned | None | **Needs API route** |
| `DocumentSyncService` | ✅ Active | Sync | Doc synchronization |
| `ExtractionIntegrationService` | ✅ Active | Pipeline | Extraction layer |
| `ExtractionLlmAdapter` | ✅ Active | Pipeline | LLM adapter |
| `HierarchicalStoryExtractionService` | ✅ Active | Peter agent | Story extraction |
| `DecisionTableExtractorService` | ✅ Active | Analysis | Business rules |
| `StateMachineExtractorService` | ✅ Active | Analysis | State patterns |
| `UiLayerExtractionService` | ✅ Active | Analysis | Frontend extraction |
| `TraceabilityService` | ✅ Active | Quality | Req-to-code tracing |
| `TraceabilityMatrixService` | ✅ Active | Quality | RTM generation |

### 6. AI/LLM (12 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `AgentService` | ✅ Active | All agents | Python↔TypeScript bridge |
| `AgentEvolutionService` | ✅ Active | Learning | Self-improvement |
| `AgentValidationLoopService` | ✅ Active | Quality gates | Iteration with gates |
| `LlmCouncilService` | ✅ Active | All workflows | 3-stage consensus |
| `StackAgentExecutor` | ✅ Active | Execution | Agent execution |
| `StackAgentFactory` | ✅ Active | Factory | Agent creation |
| `KanbanAgentService` | ✅ Active | Kanban | Board-aware ops |
| `CouncilHumanReviewService` | ✅ Active | Escalation | Human review |
| `ExperienceStoreService` | ✅ Active | Learning | ChromaDB (5 collections) |
| `ExperiencePruningService` | ✅ Active | Maintenance | Data cleanup |
| `ContinuousLearningService` | ✅ Active | Learning | Agent learning loop |
| `ThinkingPatternStore` | ✅ Active | Learning | Pattern persistence |

### 7. Quality (11 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `QualityGateIntegrationService` | ✅ Active | Quinn agent | Workflow gates |
| `KanbanQualityGateService` | ✅ Active | Kanban | 42 rules in IN_REVIEW |
| `QualityScanService` | ✅ Active | Quality workflow | Comprehensive scanning |
| `CharacterizationTestService` | ✅ Active | Tessa agent | Golden Master pattern |
| `TestOrganizationService` | ✅ Active | Testing | Test structure |
| `ValidationPipelineService` | ✅ Active | All | 5-phase validation |
| `InvestValidatorService` | ✅ Active | Peter agent | INVEST validation |
| `SpecVerificationService` | ✅ Active | Quality | Spec verification |
| `SpecReviewService` | ✅ Active | Felix+Quinn | Adversarial review |
| `SpecShapingService` | ✅ Active | Refinement | Spec refinement |
| `QuickSpecService` | ✅ Active | Rapid | Quick generation |

### 8. Integration (7 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `GitHubAnalysisService` | ✅ Active | Analysis | Hotspots, PRs, CI/CD |
| `GitHubIssuesService` | ✅ Active | Sync | Bidirectional sync |
| `AzureDevopsService` | ✅ Active | Analysis | Repo intelligence |
| `AuthorizationMatrixService` | ✅ Active | Security | RBAC extraction |
| `RequirementsSyncService` | ✅ Active | Sync | Requirements sync |
| `GitWorktreeService` | ✅ Active | Git | Worktree management |
| `CdcIntegrationService` | ✅ Active | Data | Change Data Capture |

**Missing Integrations:**
- ❌ Jira Service (not implemented)
- ❌ ServiceNow Service (not implemented)
- ❌ Slack/Teams integration (not implemented)

### 9. Estimation (8 services)

| Service | Status | Workflow Usage | Notes |
|---------|--------|----------------|-------|
| `BrownPaperEstimationService` | ✅ Active | Eliza agent | IFPUG FP |
| `BrownPaperService` | ⚠️ Review | Brown Paper | 177KB - needs refactor |
| `LoadEstimationService` | ✅ Active | Capacity | Concurrent users |
| `MigrationEstimationService` | ✅ Active | Migration | Migration effort |
| `EstimationHistoryService` | ✅ Active | Tracking | Historical accuracy |
| `ProjectAssessmentOrchestrator` | ✅ Active | Orchestrator | Assessment coordination |
| `CcpmOrchestrator` | ✅ Active | CCPM | Critical Chain PM |
| `WavePlannerService` | ✅ Active | Paul agent | Wave-based planning |

### 10. Language Analyzers (4 services)

| Service | Status | Notes |
|---------|--------|-------|
| `DotnetAnalyzerService` | ✅ Active | .NET codebase analysis |
| `FrontendAnalyzerService` | ✅ Active | Frontend frameworks |
| `PhpAnalyzerService` | ✅ Active | PHP codebases |
| `VbscriptAnalyzerService` | ✅ Active | VBScript analysis |

---

## Workflow Integration Matrix

### The 4 Main Workflows

| Workflow | Stages | Primary Agents | Service Dependencies |
|----------|--------|----------------|---------------------|
| **Brown Paper** | 6 | Miguel, Peter, Betty, Felix, Quinn, Marcus, Eliza, Diana | 15+ services |
| **Migration** | 6 | Miguel, Peter, Betty, Felix, Paul, Eliza, Quinn | 12+ services |
| **Green Paper** | 6 | Peter, Betty, Vicky, Felix, Paul, Eliza, Quinn | 10+ services |
| **Quality** | 5 | Miguel, Quinn, Marcus, Tessa | 8+ services |

### Detailed Stage-to-Service Mapping

#### Brown Paper Workflow (6 stages)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ code_understanding│ ──► │ domain_extraction │ ──► │ story_extraction │
│     (Miguel)      │     │  (Peter, Betty)   │     │     (Peter)      │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ EvolutionMetrics │     │ HierarchicalStory │     │ InvestValidator  │
│ DependencyGraph  │     │ DecisionTable     │     │ StoryExtraction  │
│ StackDetection   │     │ StateMachine      │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  deep_extraction │ ──► │    estimation    │ ──► │    output_       │
│(Felix,Quinn,Marc)│     │     (Eliza)      │     │  consolidation   │
├──────────────────┤     ├──────────────────┤     │     (Diana)      │
│ MigrationArch    │     │ FPMethodology    │     ├──────────────────┤
│ QualityGate      │     │ BrownPaperEst    │     │ MigrationReport  │
│ TechnicalDebt    │     │                  │     │ DocTemplates     │
│ SecurityScanner  │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Migration Workflow (6 stages)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ validate_answers │ ──► │technical_analysis│ ──► │generate_spec     │
│   (Orchestrator) │     │    (Miguel)      │     │  (Peter, Betty)  │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ BMAD 8 Questions │     │ EvolutionMetrics │     │ MigrationArch    │
│ Input Validation │     │ StackDetection   │     │ StranglerFig     │
│                  │     │ AsisArchitecture │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  generate_tasks  │ ──► │  estimate_effort │ ──► │  quality_review  │
│  (Felix, Paul)   │     │     (Eliza)      │     │     (Quinn)      │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ WavePlanner      │     │ FPMethodology    │     │ QualityGate      │
│ TaskGeneration   │     │ MigrationEst     │     │ MigrationSecurity│
│ ErdGenerator     │     │                  │     │ SpecReview       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Green Paper Workflow (6 stages)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ validate_vision  │ ──► │ requirements_    │ ──► │    ux_design     │
│   (Orchestrator) │     │  constitution    │     │     (Vicky)      │
│                  │     │  (Peter, Betty)  │     │                  │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ 6 GP Questions   │     │ SpecShaping      │     │ DesignOSService  │
│ Vision Validation│     │ InvestValidator  │     │ UiLayerExtraction│
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│architecture_design│──► │implementation_   │ ──► │  quality_review  │
│     (Felix)      │     │    planning      │     │     (Quinn)      │
├──────────────────┤     │  (Paul, Eliza)   │     ├──────────────────┤
│ MigrationArch    │     ├──────────────────┤     │ QualityGate      │
│ KnowledgeGraph   │     │ WavePlanner      │     │ MigrationSecurity│
│ ErdGenerator     │     │ FPMethodology    │     │ SpecReview       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Quality Workflow (5 stages)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  scan_execution  │ ──► │ metrics_analysis │ ──► │  quality_review  │
│     (Miguel)     │     │     (Miguel)     │     │     (Quinn)      │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ SecurityScanner  │     │ EvolutionMetrics │     │ QualityGate      │
│ CyberStrike      │     │ TrendAnalysis    │     │ KanbanQualityGate│
│ QualityScan      │     │ TechnicalDebt    │     │ (42 rules)       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         ▼                        ▼                        │
┌──────────────────┐     ┌──────────────────┐              │
│ remediation_     │ ──► │  test_validation │ ◄────────────┘
│   planning       │     │     (Tessa)      │   (conditional)
│    (Marcus)      │     ├──────────────────┤
├──────────────────┤     │ Characterization │
│ TechnicalDebt    │     │ CodeCoverage     │
│ ImprovementPlan  │     │ ValidationPipeline│
│ MarcusIntegration│     │                  │
└──────────────────┘     └──────────────────┘
```

### Agent-to-Service Dependencies

| Agent | Primary Services | Workflow Usage |
|-------|-----------------|----------------|
| **Miguel** | EvolutionMetricsService | Brown Paper, Migration, Quality |
| **Peter** | HierarchicalStoryExtractionService, InvestValidatorService | All except Quality |
| **Betty** | Business analysis (custom logic) | All except Quality |
| **Felix** | MigrationArchitectureService, KnowledgeGraphService | All except Quality |
| **Quinn** | QualityGateIntegrationService, MigrationSecurityService | All workflows |
| **Eliza** | FPMethodologyService, BrownPaperEstimationService | All except Quality |
| **Marcus** | MarcusAgent, TechnicalDebtService | Brown Paper, Quality |
| **Diana** | MigrationReportService, DocumentationTemplates | Brown Paper |
| **Vicky** | DesignOSService, VickyAgentService | Green Paper only |
| **Paul** | WavePlannerService | Migration, Green Paper |
| **Tessa** | CharacterizationTestService, CodeCoverageAnalyzerService | Quality only |

---

## Services NOT Yet Integrated

### Orphaned Services (Complete but No Integration)

These services are fully implemented with unit tests but lack API routes and workflow integration:

| Service | Fase | Category | Required Integration |
|---------|------|----------|---------------------|
| **RiskHeatMapService** | 24-A4 | Visualization | API route + Quality workflow |
| **VisualDependencyGraphService** | 24-E1 | Visualization | API route + Brown Paper workflow |
| **ContextAwareDocumentationService** | 24-J1 | Documentation | API route + Diana agent |
| **DatabaseFirstMigrationService** | 24-D2 | Migration | API route + Migration workflow |

### Integration Action Plan

```python
# Required API Routes (to create)
POST /api/risk-analysis/heat-map          # RiskHeatMapService
GET  /api/risk-analysis/heat-map/{id}
POST /api/dependency-analysis/visual      # VisualDependencyGraphService
GET  /api/dependency-analysis/visual/{id}
POST /api/documentation/auto-generate     # ContextAwareDocumentationService
GET  /api/documentation/auto/{id}
POST /api/migration/database-first        # DatabaseFirstMigrationService
GET  /api/migration/database-first/{id}

# Required main.py registration
app.include_router(risk_heat_map.router)
app.include_router(visual_dependency_graph.router)
app.include_router(auto_documentation.router)
app.include_router(database_first_migration.router)

# Required workflow hooks
- Quality workflow: Add RiskHeatMapService to scan_execution stage
- Brown Paper workflow: Add VisualDependencyGraphService to code_understanding stage
- Brown Paper workflow: Add ContextAwareDocumentationService to output_consolidation stage
- Migration workflow: Add DatabaseFirstMigrationService to technical_analysis stage
```

### Missing Platform Integrations

| Integration | Fase | Priority | Notes |
|-------------|------|----------|-------|
| **Jira** | 28 | HIGH | No service exists |
| **ServiceNow** | 28 | MEDIUM | No service exists |
| **Slack** | - | LOW | No service exists |
| **MS Teams** | - | LOW | No service exists |
| **MS Project Export** | 24-M1 | MEDIUM | Not implemented |

---

## Cleanup Recommendations

### High Priority - Remove/Consolidate

| Item | Issue | Recommendation | Impact |
|------|-------|----------------|--------|
| **brown_paper_service.py** | 177KB, oversized | Split into focused modules | HIGH |
| **CyberStrike vs GhostCrew** | Overlapping security scanners | Consolidate into unified scanner | MEDIUM |
| **Ora2pg + Sqlines wrappers** | Duplicate transformation | Merge into CodeTransformationService | LOW |
| **MigrationEnhancedService** | Unclear distinction from base | Review and consolidate | LOW |

### Detailed Recommendations

#### 1. brown_paper_service.py (177KB) - SPLIT REQUIRED

```
Current: 1 file, 177KB
         ├── Session management
         ├── Extraction logic
         ├── Estimation integration
         ├── Report generation
         └── Export functionality

Proposed Split:
backend/app/services/brown_paper/
├── __init__.py
├── session_service.py        # Session lifecycle
├── extraction_service.py     # Code/domain extraction
├── estimation_adapter.py     # Eliza integration
├── report_generator.py       # Output generation
└── export_service.py         # Multi-format export
```

#### 2. Security Scanner Consolidation

```
Current:
├── cyberstrike_service.py    # OWASP, Bandit, Safety, Semgrep
├── ghostcrew_service.py      # Multi-mode scanning
├── security_workflow_service.py
└── security_scanner/
    └── orchestrator.py       # Scanner coordination

Recommendation:
- Keep: security_scanner/orchestrator.py as primary entry point
- Merge: CyberStrike and GhostCrew logic into orchestrator
- Deprecate: ghostcrew_service.py (mode logic can be config)
- Reason: Reduce cognitive load, single security entry point
```

#### 3. Code Transformation Wrappers

```
Current:
├── code_transformation_service.py  # VB→C#, T-SQL→PL/pgSQL
├── ora2pg_wrapper_service.py       # Oracle→PostgreSQL
└── sqlines_wrapper_service.py      # SQL Server→PostgreSQL

Recommendation:
- Keep: code_transformation_service.py as primary
- Integrate: ora2pg and sqlines as adapters within transformation service
- Reason: Single transformation entry point with backend adapters
```

### Services Safe to Remove

| Service | Reason | Replacement |
|---------|--------|-------------|
| `noqa_service.py` | Not found in codebase | N/A |
| Duplicate wrappers | Consolidated into main service | Main service |
| Old experiment services | No longer used | None needed |

### Services to Keep (Despite Overlap)

| Service | Reason to Keep |
|---------|----------------|
| `MigrationArchitectureService` | Distinct from MigrationAnalyzerService (target vs source) |
| `QualityScanService` | Distinct from QualityGateIntegrationService (scan vs gate) |
| `ExperienceStoreService` | Active learning, ChromaDB (5 collections) |

---

## Appendix: Agent Roles

### Agent Roster (11 Agents)

| Agent | Specialty | Primary Services | Workflows |
|-------|-----------|-----------------|-----------|
| **Miguel** | Metrics Specialist | EvolutionMetricsService | BP, MG, QA |
| **Peter** | Product Owner | HierarchicalStoryExtractionService | BP, MG, GP |
| **Betty** | Business Analyst | Custom business logic | BP, MG, GP |
| **Felix** | Architecture | MigrationArchitectureService | BP, MG, GP |
| **Quinn** | Quality | QualityGateIntegrationService | All 4 |
| **Eliza** | Estimation | FPMethodologyService | BP, MG, GP |
| **Marcus** | Maintenance | TechnicalDebtService, MarcusAgent | BP, QA |
| **Diana** | Documentation | MigrationReportService | BP |
| **Vicky** | Visual Design | DesignOSService | GP |
| **Paul** | Planning | WavePlannerService | MG, GP |
| **Tessa** | Testing | CharacterizationTestService | QA |

**Legend:** BP=Brown Paper, MG=Migration, GP=Green Paper, QA=Quality

### Agent Workload Distribution

```
Workflow Coverage:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Quinn ████████████████████████████████████████████  (4/4 workflows) │
│  Peter ██████████████████████████████               (3/4 workflows)  │
│  Betty ██████████████████████████████               (3/4 workflows)  │
│  Felix ██████████████████████████████               (3/4 workflows)  │
│  Eliza ██████████████████████████████               (3/4 workflows)  │
│  Miguel █████████████████████████████               (3/4 workflows)  │
│  Marcus ████████████████████                        (2/4 workflows)  │
│  Paul   ████████████████████                        (2/4 workflows)  │
│  Diana  ██████████                                  (1/4 workflows)  │
│  Vicky  ██████████                                  (1/4 workflows)  │
│  Tessa  ██████████                                  (1/4 workflows)  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-15 | Claude Code | Initial comprehensive document |

---

*Generated: Week 158 (2026-01-15)*
