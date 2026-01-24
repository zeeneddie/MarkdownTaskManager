# Migration Ecosystem Assessment

**Fase 0 Discovery - Week 158**

## 1. Executive Summary

Het bestaande migration ecosysteem bevat **111 endpoints** in **10 categorieën** met **17 code-gedreven services**. De architectuur ondersteunt al grotendeels de gewenste "Software Intake" functionaliteit. De 8-question MarQed workflow zit **alleen** in de BrownPaperService en kan worden losgekoppeld.

**Conclusie**: Refactor de bestaande services, geen nieuwbouw nodig.

---

## 2. Service Categorisatie

### 2.1 Code-Gedreven Services (100% automatisch)

Deze services werken puur op `project_path` zonder gebruikersinput:

| Service | Functie | Input | Output |
|---------|---------|-------|--------|
| `MigrationAnalyzerService` | 5-fase orchestrator | `repo_path` | Detection, stack analysis, DB analysis, cross-cutting |
| `MigrationSecurityService` | OWASP security scanning | `directory` | Vulnerabilities, risk score, recommendations |
| `MigrationEstimationService` | IFPUG Function Points | `directory`, `source_stack` | FP calculation, phase estimates, effort |
| `MigrationArchitectureService` | Architecture recommendations | `directory` | Patterns, component mapping, ADRs |
| `DatabaseAnalyzerService` | Database schema analysis | `connection_string` | Tables, procedures, relationships |
| `DotNetAnalyzerService` | .NET code analysis | `project_path` | Classes, dependencies, WCF services |
| `FrontendAnalyzerService` | Frontend analysis | `project_path` | React/Angular/Vue components |
| `PHPAnalyzerService` | PHP code analysis | `directory` | Classes, functions, Laravel/Symfony patterns |
| `VBScriptAnalyzerService` | VBScript analysis | `directory` | ASP Classic patterns, security issues |
| `StoredProcedureAnalyzerService` | SP analysis | `directory` | T-SQL/PL-SQL procedures |
| `SQLAnalysisService` | SQL analysis | `directory` | Queries, tables, joins |
| `CodeAnalysisAggregatorService` | Multi-analyzer orchestrator | `project_path` | Combined analysis |
| `DependencyGraphService` | Dependency mapping | `project_path` | Dependency graph, cycles |
| `LayeredAnalysisService` | Layered architecture | `project_path` | Layer identification |
| `DeepExtractionService` | Deep code extraction | `project_path` | Business rules, entities |
| `HierarchicalStoryExtractionService` | Story extraction | `project_path` | User stories from code |
| `UILayerExtractionService` | UI component extraction | `project_path` | Screens, forms, controls |
| `LibraryMigrationMapperService` | Library mapping | `project_path` | NuGet/NPM equivalents |

### 2.2 Vraag-Gedreven Services (Hybrid)

| Service | Functie | Vraag-Afhankelijkheid |
|---------|---------|----------------------|
| `BrownPaperService` | MarQed workflow | 8 vragen (Brown Paper) / 6 vragen (Green Paper) |
| `MigrationEnhancedService` | 7-fase execution | Configuratie input (target stack, strategy) |

---

## 3. Endpoint Catalogus

### 3.1 Per Categorie

| Categorie | Endpoints | Code-Gedreven | Vraag-Gedreven |
|-----------|-----------|---------------|----------------|
| `intake` | 10 | 2 | 8 |
| `migration` | 19 | 19 | 0 |
| `migration-architecture` | 13 | 13 | 0 |
| `migration-estimation` | 10 | 10 | 0 |
| `migration-execution` | 28 | 28 | 0 |
| `migration-report` | 10 | 10 | 0 |
| `migration-security` | 9 | 9 | 0 |
| `v2` | 6 | 6 | 0 |
| `week131` | 5 | 5 | 0 |
| **Totaal** | **110** | **102** | **8** |

### 3.2 Key Endpoints per Service

**MigrationAnalyzerService (19 endpoints)**
- `POST /migration/analyze/create` - Start new analysis (repo_path)
- `POST /migration/analyze/{id}/run` - Execute full analysis
- `GET /migration/analyze/{id}` - Get analysis results
- `GET /migration/analyze/{id}/phases` - Get phase progress

**MigrationSecurityService (9 endpoints)**
- `POST /migration/security/scan` - Scan directory for OWASP issues
- `GET /migration/security/patterns` - List detectable patterns
- `GET /migration/security/{id}/findings` - Get findings

**MigrationEstimationService (10 endpoints)**
- `POST /migration/estimation/analyze` - Estimate effort (directory)
- `GET /migration/estimation/stacks` - List supported stacks
- `GET /migration/estimation/{id}` - Get estimation result

**MigrationArchitectureService (13 endpoints)**
- `POST /migration/architecture/recommend` - Generate recommendations
- `POST /migration/architecture/adr` - Generate ADRs
- `GET /migration/architecture/patterns` - List patterns

**MigrationExecutionService (28 endpoints)**
- `POST /migration/execution/strangler/init` - Initialize Strangler Fig
- `POST /migration/execution/wave/plan` - Generate wave plan
- `POST /migration/execution/ui/extract` - Extract UI components
- `POST /migration/execution/library/map` - Map libraries

---

## 4. Service Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    MigrationAnalyzerService                     │
│                     (Miguel Orchestrator)                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ DatabaseAnalyzer│ │ DotNetAnalyzer  │ │FrontendAnalyzer │
│    Service      │ │    Service      │ │    Service      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│MigrationSecurity│ │MigrationEstim.  │ │MigrationArch.   │
│    Service      │ │    Service      │ │    Service      │
│    (Quinn)      │ │    (FP Calc)    │ │    (Felix)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 5. Gap Analyse

### 5.1 Wat Werkt (Software Intake)

De `MigrationAnalyzerService` implementeert al 5 fasen:
1. **Detection** (0-20%) - Scan files, detect stacks
2. **Stack Analysis** (20-50%) - Run relevant analyzers
3. **DB Analysis** (50-70%) - Analyze database schemas
4. **Cross-Cutting** (70-90%) - Security, FP, architecture
5. **Output** (90-100%) - Generate reports

Output bevat:
- LOC, file counts per type
- Detected frameworks/stacks
- Security vulnerabilities (OWASP)
- Function Points + effort estimate
- Business rules extracted
- Dependency graph
- Architecture recommendations

### 5.2 Wat Ontbreekt

| Gap | Impact | Oplossing |
|-----|--------|-----------|
| Unified JSON output schema | Medium | Standaardiseer output format |
| API voor pure code-analyse zonder sessie | High | Nieuwe endpoint `/api/v3/intake/analyze` |
| Streaming progress updates | Medium | WebSocket/SSE integratie |
| Caching van analyses | Low | Redis caching layer |

### 5.3 Vraag-Driven Locaties

De 8 MarQed vragen zitten ALLEEN in:
- `app/services/brown_paper_service.py` (MarQedSession persistence)
- `app/confucius/workflows/migration.py` (MigrationOrchestrator)
- `app/api/confucius_workflows.py` (API endpoints)

---

## 6. Refactor Strategie

### 6.1 Aanbevolen Aanpak: Facade Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    SoftwareIntakeService                        │
│              (Nieuwe Facade - geen vragen)                      │
│                                                                 │
│  def analyze(project_path: str) -> IntakeReport:               │
│      1. Call MigrationAnalyzerService.run_analysis()           │
│      2. Call MigrationSecurityService.analyze_directory()      │
│      3. Call MigrationEstimationService.analyze_directory()    │
│      4. Call MigrationArchitectureService.analyze_directory()  │
│      5. Aggregate to unified JSON                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ produces
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       IntakeReport                              │
│  {                                                              │
│    "project_path": "/path/to/project",                         │
│    "analyzed_at": "2024-01-15T10:30:00Z",                      │
│    "summary": {...},                                            │
│    "code_metrics": {...},                                       │
│    "security": {...},                                           │
│    "estimation": {...},                                         │
│    "architecture": {...},                                       │
│    "recommendations": [...]                                     │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ feeds into
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MigrationPlanningService                     │
│              (Hernoem van MarQed/BrownPaper)                   │
│                                                                 │
│  def plan(                                                      │
│      intake_report: IntakeReport,                              │
│      why: str,           # Business question 1                  │
│      stakeholders: str,  # Business question 2                  │
│      timeline: str       # Business question 3                  │
│  ) -> MigrationPlan                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Implementatie Fasen

**Fase 1: SoftwareIntakeService (nieuw)**
- Nieuwe service die bestaande analyzers orchestreert
- Output: `IntakeReport` JSON schema
- Geen database sessie nodig
- Endpoint: `POST /api/v3/intake/analyze`

**Fase 2: Rename BrownPaper → MigrationPlanning**
- Hernoem service en models
- Verwijder 8-question dependency
- Maak IntakeReport verplichte input

**Fase 3: Simplify MarQed Questions**
- Reduceer tot 3 business vragen (waarom, wie, wanneer)
- Focus op planning, niet analyse

---

## 7. Tijdlijn Schatting

| Fase | Omvang | Risico |
|------|--------|--------|
| Fase 1: SoftwareIntakeService | ~200 regels nieuwe code | Laag - composeert bestaande services |
| Fase 2: Rename BrownPaper | ~50 files aanpassen | Medium - veel referenties |
| Fase 3: Simplify Questions | ~100 regels wijzigen | Laag - lokale wijziging |

---

## 8. Conclusie

**Strategie**: Refactor, geen nieuwbouw

Het bestaande ecosysteem bevat 102 van 110 endpoints die al code-gedreven zijn. De enige vraag-afhankelijkheid zit in de BrownPaperService die kan worden ontkoppeld met een nieuwe SoftwareIntakeService facade.

**Volgende Stappen**:
1. Definieer `IntakeReport` JSON schema
2. Implementeer `SoftwareIntakeService` als facade
3. Creëer nieuwe API endpoint `/api/v3/intake/analyze`
4. Hernoem BrownPaper → MigrationPlanning
5. Update MarQed workflow voor 3 business vragen

---

## Appendix A: Ondersteunde Technologie Stacks

### Source Stacks (gedetecteerd)
- VB.NET WebForms
- C# WebForms
- Classic ASP
- PHP Legacy (4.x, 5.x)
- Java Legacy (Struts, JSP)
- ColdFusion
- Perl CGI
- COBOL
- Oracle Forms
- PowerBuilder

### Target Stacks
- .NET 8
- Python FastAPI
- Node.js NestJS
- Java Spring Boot
- Go Fiber

### Databases
- SQL Server → PostgreSQL
- Oracle → PostgreSQL
- MySQL → PostgreSQL
- Access → PostgreSQL

---

## Appendix B: Bestaande Migration Types

```python
class MigrationType(Enum):
    MODERNIZE = "modernize"      # Legacy → Modern stack
    CONSOLIDATE = "consolidate"  # Multiple apps → Single app
    HYBRID = "hybrid"            # Phased approach
```

## Appendix C: Bestaande Migration Strategies

```python
class MigrationStrategy(Enum):
    STRANGLER_FIG = "strangler_fig"
    BIG_BANG = "big_bang"
    PARALLEL_RUN = "parallel_run"
    INCREMENTAL = "incremental"
    PHASED = "phased"
    BLUE_GREEN = "blue_green"
```
