# Workflow & Service Discovery Report

**Datum**: 2026-01-28
**Versie**: 1.0
**Status**: Initiële Discovery

---

## Executive Summary

| Metric | Waarde |
|--------|--------|
| **Totaal Services** | 187 |
| **Categorieën** | 17 |
| **Workflow-gerelateerd** | 59 services |
| **Ondersteunend** | 128 services |

---

## Service Categorieën Overzicht

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE ARCHITECTUUR                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      WORKFLOW SERVICES (59)                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  CONFUCIUS (6)     EXTRACTION (5)    KANBAN (7)      GRAPH (6)      │   │
│  │  ├─ Brown Paper    ├─ Deep           ├─ Agent        ├─ Dependency  │   │
│  │  ├─ Migration      ├─ Hierarchical   ├─ Events       ├─ Knowledge   │   │
│  │  ├─ Architecture   ├─ UI Layer       ├─ Quality Gate ├─ Visual      │   │
│  │  └─ Planning       └─ Integration    ├─ Lane Prog    └─ Shadow      │   │
│  │                                      └─ Dashboard                    │   │
│  │                                                                      │   │
│  │  PROJECT (5)       QUALITY (3)       AGENT (4)       CCPM (2)       │   │
│  │  ├─ Intake         ├─ Quality Gate   ├─ Evolution    ├─ Orchestr    │   │
│  │  ├─ Wizard         ├─ INVEST         ├─ Validation   └─ Worktree    │   │
│  │  ├─ Assessment     └─ Spec Shaping   └─ GhostCrew                   │   │
│  │  └─ Backlog                                                          │   │
│  │                                                                      │   │
│  │  ANALYSIS (4)      ESTIMATION (3)    LLM (2)         SECURITY (2)   │   │
│  │  ├─ CiRA           ├─ Load           ├─ Council      ├─ AuthMatrix  │   │
│  │  ├─ Code Aggreg    ├─ Migration      └─ Human Rev    └─ Workflow    │   │
│  │  ├─ Layered        └─ History                                        │   │
│  │  └─ SWOT                                                             │   │
│  │                                                                      │   │
│  │  DATABASE (3)      DEVOPS (3)        TESTING (2)     DOCS (2)       │   │
│  │  ├─ Migration      ├─ Azure DevOps   ├─ Character    ├─ CodeWiki    │   │
│  │  ├─ Patterns       ├─ GitHub         └─ Test Org     └─ Context     │   │
│  │  └─ StoredProc     └─ Issues                                         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SUPPORTING SERVICES (128)                         │   │
│  │         Infrastructure, Utilities, Adapters, Analyzers              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Documentatie Links

| Workflow Categorie | Documentatie |
|-------------------|--------------|
| **Confucius** | [confucius/index.md](confucius/index.md) |
| **Extraction** | [extraction/index.md](extraction/index.md) |
| **Architecture** | [architecture/dependency-matrix.md](architecture/dependency-matrix.md) |

---

## 1. CONFUCIUS WORKFLOWS (6 services)

> **Volledige Documentatie**: [confucius/index.md](confucius/index.md)

De kern workflows voor legacy migratie analyse met 4 workflow orchestrators.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **brown_paper_service.py** | 188 KB | Legacy code analyse & migratie planning | BrownPaperService, MarQedBrownPaperWorkflow |
| **brown_paper_estimation_service.py** | 16 KB | Function Point & Story Point schatting | BrownPaperEstimationService |
| **migration_analyzer_service.py** | 50 KB | Code analyse voor migratie | MigrationAnalyzerService |
| **migration_architecture_service.py** | 45 KB | Architectuur planning | ArchitecturePattern, TechnologyChoice |
| **migration_enhanced_service.py** | 32 KB | Enhanced analyse features | MigrationEnhancedService |
| **migration_planning_orchestrator.py** | 42 KB | Orchestratie van migratie planning | MigrationPlanningOrchestrator |

### User Journey: Brown Paper Workflow

```
[Gebruiker] "Ik wil legacy code analyseren voor migratie"
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   START     │───▶│   VRAGEN    │───▶│   ANALYSE   │───▶│   TASKS     │
│   Sessie    │    │   1-8       │    │   Miguel    │    │   Felix     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │
     ▼                   ▼                  ▼                  ▼
 session_id         answers[]          complexity         epics/stories
                                      risk_register       story_points
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  ENHANCED   │
                                    │  ANALYSIS   │
                                    │  (6 phases) │
                                    └─────────────┘
```

---

## 2. EXTRACTION WORKFLOWS (5 services)

Services voor het extraheren van business logica uit code.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **deep_extraction_service.py** | 101 KB | Diepgaande code extractie | DeepExtractionService |
| **hierarchical_story_extraction_service.py** | 61 KB | Epic/Feature/Story extractie | ExtractedStory, StoryConfidence |
| **ui_layer_extraction_service.py** | 37 KB | UI componenten extractie | UIFramework, LegacyUIType |
| **extraction_integration_service.py** | 18 KB | Integratie met Kanban | ExtractionIntegrationService |
| **extraction_llm_adapter.py** | 45 KB | LLM prompts voor extractie | ExtractionPrompts |

### User Journey: Story Extraction

```
[Code Analyse Resultaat]
     │
     ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  HIERARCHICAL   │───▶│     DEEP        │───▶│   INTEGRATION   │
│  EXTRACTION     │    │   EXTRACTION    │    │   (naar Kanban) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     │                        │                       │
     ▼                        ▼                       ▼
 Epics/Features          Gedetailleerde          Backlog items
 /Stories               business rules          in Kanban board
```

---

## 3. KANBAN WORKFLOWS (7 services)

AI-gestuurde Kanban board management.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **kanban_agent_service.py** | 29 KB | AI agent voor Kanban | AgentName, DoDStatus |
| **kanban_event_service.py** | 28 KB | Event handling | KanbanLane, EventType |
| **kanban_quality_gate_service.py** | 50 KB | Quality gates per lane | ValidationRule, ValidationResult |
| **lane_progression_service.py** | 28 KB | Lane transitie logica | LaneGate, AgentResult |
| **complexity_dashboard_service.py** | 31 KB | Complexity metrics | ModuleHealthStatus |
| **evolution_dashboard_service.py** | 26 KB | Evolution tracking | TrendDirection |
| **personalized_dashboard_service.py** | 17 KB | Gepersonaliseerde views | - |

### User Journey: Kanban Workflow

```
[Story in Backlog]
     │
     ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ BACKLOG │──▶│  TODO   │──▶│ IN PROG │──▶│ REVIEW  │──▶│  DONE   │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     │             │             │             │             │
     ▼             ▼             ▼             ▼             ▼
  Quality       Quality       Quality       Quality       Archive
   Gate          Gate          Gate          Gate
     │             │             │             │
     ▼             ▼             ▼             ▼
  AI Agent     AI Agent     AI Agent     AI Agent
  validates    validates    validates    validates
```

---

## 4. GRAPH WORKFLOWS (6 services)

Dependency en knowledge graph services.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **dependency_graph_service.py** | 31 KB | Code dependency analyse | DependencyEdge, Language |
| **graph_workflow_service.py** | 40 KB | Graph-based workflows | GraphWorkflowService |
| **graph_workflow_integration_service.py** | 35 KB | Integratie met andere services | - |
| **knowledge_graph_service.py** | 25 KB | Knowledge base | EntityType, RelationType |
| **visual_dependency_graph_service.py** | 21 KB | Visualisatie | LayoutType, NodeShape |
| **shadow_graph_service.py** | 23 KB | Shadow dependencies | - |

---

## 5. PROJECT WORKFLOWS (5 services)

Project intake en setup workflows.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **software_intake_service.py** | 57 KB | Nieuwe project intake | AnalysisPhase, SoftwareIntakeService |
| **project_assessment_orchestrator.py** | 79 KB | Project beoordeling | PhaseResult, VerboseConfig |
| **intake_to_backlog_service.py** | 55 KB | Intake naar backlog conversie | DomainType, EpicType |
| **project_wizard_service.py** | 18 KB | Project setup wizard | TechStackConfig, TeamMemberConfig |
| **project_service.py** | 10 KB | Basis project CRUD | ProjectService |

### User Journey: Project Intake

```
[Nieuwe klant/project]
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INTAKE    │───▶│ ASSESSMENT  │───▶│   WIZARD    │───▶│  BACKLOG    │
│   Form      │    │   Analyse   │    │   Config    │    │   Setup     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │
     ▼                   ▼                  ▼                  ▼
 Basis info         Tech stack          Team setup        Initiële
 verzameld          gedetecteerd        compleet          stories
```

---

## 6. QUALITY WORKFLOWS (3 services)

Quality assurance en validatie.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **quality_gate_integration_service.py** | 21 KB | Quality gate checks | QualityGateResult |
| **invest_validator_service.py** | 40 KB | INVEST criteria validatie | ValidationLevel, CriterionStatus |
| **spec_shaping_service.py** | 16 KB | Specificatie refinement | CheckCategory, VerificationResult |

---

## 7. AGENT WORKFLOWS (4 services)

AI agent management en evolution.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **agent_service.py** | 77 KB | Centrale agent management | AgentService |
| **agent_evolution_service.py** | 32 KB | Agent learning & improvement | TaskContext, Guidance |
| **agent_validation_loop_service.py** | 16 KB | Validation feedback loops | ValidationAttempt, FixSuggestion |
| **ghostcrew_service.py** | 39 KB | Multi-agent orchestratie | GhostCrewService |

---

## 8. ANALYSIS SERVICES (4 services)

Code en business analyse.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **code_analysis_aggregator_service.py** | 19 KB | Aggregatie van analyses | TechnologyProfile, DependencyProfile |
| **layered_analysis_service.py** | 21 KB | Gelaagde analyse | LayeredAnalysisService |
| **cira_service.py** | 44 KB | Causal relationship analyse | CausalRelationExtractor |
| **swot_generator_service.py** | 30 KB | SWOT analyse generatie | SWOTItem, FindingCategory |

---

## 9. CCPM WORKFLOWS (2 services)

Critical Chain Project Management.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **ccpm_orchestrator.py** | 24 KB | CCPM orchestratie | DecompositionResult, CCPMOrchestrator |
| **ccpm_workflow_integration_service.py** | 21 KB | Git worktree integration | WorkflowWorktreeSession |

---

## 10. DATABASE SERVICES (3 services)

Database analyse en migratie.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **stored_procedure_analyzer_service.py** | 38 KB | SP analyse | StoredProcedure, ComplexityLevel |
| **database_migration_pattern_service.py** | 50 KB | Migratie patronen | MigrationPatternType, RiskLevel |
| **database_migration_executor_service.py** | 21 KB | Migratie executie | DatabaseType, MigrationPhase |

---

## 11. DEVOPS SERVICES (3 services)

DevOps integraties.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **azure_devops_service.py** | 35 KB | Azure DevOps integratie | AzureDevOpsService |
| **github_analysis_service.py** | 31 KB | GitHub analyse | GitHubConfig, HotSpotData |
| **github_issues_service.py** | 22 KB | GitHub Issues sync | GitHubIssue, SyncResult |

---

## 12. LLM SERVICES (2 services)

LLM integratie en council.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **llm_council_service.py** | 32 KB | Multi-LLM council | LLMCouncilService |
| **council_human_review_service.py** | 24 KB | Human-in-the-loop | CouncilHumanReviewService |

---

## 13. ESTIMATION SERVICES (3 services)

Schattingen en voorspellingen.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **migration_estimation_service.py** | 34 KB | Migratie schattingen | MigrationPhase, ComponentType |
| **load_estimation_service.py** | 25 KB | Load/performance schatting | LoadEstimationService |
| **estimation_history_service.py** | 24 KB | Historische data | EstimationHistoryService |

---

## 14. SECURITY SERVICES (2 services)

Security en autorisatie.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **authorization_matrix_service.py** | 34 KB | Autorisatie matrix | AuthorizationMatrixService |
| **security_workflow_service.py** | 25 KB | Security gates | SecurityGateDecision |

---

## 15. TESTING SERVICES (2 services)

Test gerelateerde services.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **characterization_test_service.py** | 18 KB | Legacy code tests | CharacterizationTestService |
| **test_organization_service.py** | 12 KB | Test organisatie | TestType, TestStatus |

---

## 16. DOCUMENTATION SERVICES (2 services)

Documentatie generatie.

| Service | Grootte | Doel | Key Classes |
|---------|---------|------|-------------|
| **codewiki_service.py** | 27 KB | Code wiki generatie | CodeWikiService |
| **context_aware_documentation_service.py** | 26 KB | Context-aware docs | DocType, DocFormat |

---

## 17. OTHER SERVICES (128 services)

Ondersteunende en gespecialiseerde services. Zie appendix voor volledige lijst.

### Highlights

| Service | Grootte | Doel |
|---------|---------|------|
| **workflow_tool_integration_service.py** | 103 KB | Tool integratie |
| **technical_debt_service.py** | 51 KB | Technical debt analyse |
| **cyberstrike_service.py** | 50 KB | Security scanning |
| **design_os_service.py** | 54 KB | Design system |
| **traceability_matrix_service.py** | 43 KB | Traceability |

---

## Dependency Matrix (Top 10 Workflows)

```
                          DEPENDENCIES
                    ┌─────────────────────────────────────────┐
                    │ Dep │ Code│ Extr│ SWOT│ LLM │ Agent│ DB │
┌───────────────────┼─────┼─────┼─────┼─────┼─────┼──────┼────┤
│ Brown Paper       │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓   │ ✓  │
│ Migration Analyzer│  ✓  │  ✓  │     │  ✓  │  ✓  │      │ ✓  │
│ Deep Extraction   │  ✓  │     │     │     │  ✓  │      │ ✓  │
│ Hierarchical Extr │     │     │  ✓  │     │  ✓  │      │ ✓  │
│ Kanban Agent      │     │     │     │     │  ✓  │  ✓   │ ✓  │
│ Project Intake    │  ✓  │  ✓  │  ✓  │     │  ✓  │      │ ✓  │
│ Quality Gate      │     │     │     │     │     │  ✓   │ ✓  │
│ CCPM Orchestrator │     │     │     │     │     │      │ ✓  │
└───────────────────┴─────┴─────┴─────┴─────┴─────┴──────┴────┘

Legenda:
- Dep = Dependency Graph Service
- Code = Code Analysis Aggregator
- Extr = Extraction Services
- SWOT = SWOT Generator
- LLM = LLM Council/Adapter
- Agent = Agent Service
- DB = Database Services
```

---

---

## API Endpoints Overzicht

| Categorie | Endpoints |
|-----------|-----------|
| **Totaal API Files** | 120 |
| **Totaal Endpoints** | 1,637 |

### Key Workflow Endpoints

#### Brown Paper (31 endpoints)

| Method | Endpoint | Doel |
|--------|----------|------|
| POST | `/api/brown-paper/marqed/start` | Start MarQed sessie |
| POST | `/api/brown-paper/marqed/{id}/answer` | Beantwoord vraag |
| GET | `/api/brown-paper/marqed/{id}/status` | Sessie status |
| POST | `/api/brown-paper/marqed/{id}/analyze` | Start analyse (Miguel) |
| POST | `/api/brown-paper/marqed/{id}/specification` | Genereer spec (Peter) |
| POST | `/api/brown-paper/marqed/{id}/tasks` | Genereer tasks (Felix) |
| POST | `/api/brown-paper/marqed/{id}/enhanced-analyze` | 6-phase enhanced analyse |
| GET | `/api/brown-paper/marqed/{id}/dependency-graph` | Dependency visualisatie |
| GET | `/api/brown-paper/marqed/{id}/hierarchy` | Epic/Feature/Story hierarchie |
| GET | `/api/brown-paper/marqed/{id}/metrics` | Code metrics |
| GET | `/api/brown-paper/marqed/{id}/export` | Export resultaten |

#### Confucius Workflows (14 endpoints)

| Method | Endpoint | Doel |
|--------|----------|------|
| POST | `/confucius/workflows/brown-paper/start` | Start Brown Paper workflow |
| POST | `/confucius/workflows/migration/start` | Start Migration workflow |
| POST | `/confucius/workflows/green-paper/start` | Start Green Paper workflow |
| POST | `/confucius/workflows/quality/start` | Start Quality workflow |
| GET | `/confucius/workflows/status/{id}` | Workflow status |
| GET | `/confucius/workflows/result/{id}` | Workflow resultaat |
| GET | `/confucius/workflows/stream/{id}` | SSE stream voor updates |

---

## Volgende Stappen

1. **[DONE]** Service inventarisatie
2. **[DONE]** API endpoint mapping
3. **[IN PROGRESS]** Confucius workflow deep-dive documentatie
4. **[TODO]** Extraction workflow deep-dive documentatie
5. **[TODO]** Volledige dependency matrix
6. **[TODO]** User journey diagrammen per workflow

---

## Appendix: Alle Services per Categorie

Zie bijlage voor de volledige lijst van 128 "other" services met hun grootte en key classes.
