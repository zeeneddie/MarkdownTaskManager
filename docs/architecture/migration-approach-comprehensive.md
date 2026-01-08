# Comprehensive Migration Approach - MarQed AI Agent Platform

**Datum:** 2025-12-31
**Week:** 129
**Project:** HCI-CRS Afspraak Module → Dual-Stack Migration
**Status:** IN PROGRESS

---

## 1. Executive Summary

Dit document beschrijft de complete migratie-aanpak die we implementeren voor de HCI-CRS Afspraak module. We voeren een **dual-stack migratie** uit: parallel naar zowel .NET 8/Blazor als Python Django/React, met dezelfde database en identieke UI als de legacy applicatie.

### Key Beslissingen

| Beslissing | Keuze | Rationale |
|------------|-------|-----------|
| Migratie Strategie | Dual-Stack Parallel | Evaluatie welke stack beter past |
| Database | SQL Server (behouden) | Beide stacks gebruiken dezelfde DB |
| UI Requirement | Pixel-perfect legacy match | Gebruikers merken geen verschil |
| Test Strategy | Per stack apart | Onafhankelijke test suites |
| ORM | EF Core 8 / Django ORM | Beide stacks eigen ORM |

---

## 2. Architectuur Overzicht

### 2.1 Source (Legacy)

```
┌─────────────────────────────────────────────────────────────────┐
│  HCI-CRS AFSPRAAK MODULE (Legacy)                                │
│                                                                  │
│  Technology: VB.NET + ASP.NET WebForms                          │
│  Database: SQL Server                                            │
│  Files: 177 (87 VB.NET, 8 ASPX, 24 SQL, 58 other)               │
│  LOC: 12,605                                                     │
│                                                                  │
│  Architectuur:                                                   │
│  ├── DAL (12 classes) - Data Access Layer                       │
│  ├── BLL (12 managers) - Business Logic Layer                   │
│  ├── WEB (8 pages) - ASP.NET WebForms                           │
│  └── Entities (12) - Domain entities                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Target Stacks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DUAL-STACK MIGRATION                                                        │
│                                                                              │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐         │
│  │  STACK A: .NET 8/Blazor     │    │  STACK B: Django/React      │         │
│  ├─────────────────────────────┤    ├─────────────────────────────┤         │
│  │ Backend: ASP.NET Core 8     │    │ Backend: Django 5.1         │         │
│  │ Frontend: Blazor Server     │    │ Frontend: React 18 + TS     │         │
│  │ ORM: EF Core 8              │    │ ORM: Django ORM             │         │
│  │ API: REST + SignalR         │    │ API: DRF + WebSockets       │         │
│  │ Auth: ASP.NET Identity      │    │ Auth: Django Auth + JWT     │         │
│  └─────────────────────────────┘    └─────────────────────────────┘         │
│                                                                              │
│                          ┌─────────────────┐                                │
│                          │   SQL Server    │ ◄── Shared Database            │
│                          │   (behouden)    │                                │
│                          └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Extraction Pipeline

### 3.1 Implemented Services (Week 128-129) ✅

| Service | Agent | Input | Output | Status |
|---------|-------|-------|--------|--------|
| **FoundationDetectionService** | Miguel | Source path | Foundation modules + categories | ✅ COMPLETE |
| **DependencyGraphService** | Miguel | Source path | Graph structure, circular deps | ✅ COMPLETE |
| **CodeAnalysisAggregatorService** | Miguel | Source path | Complexity, coupling, cohesion | ✅ COMPLETE |
| **LayeredAnalysisService** | Miguel | Source path | VBScript, stored procs, ASP | ✅ COMPLETE |

### 3.2 Foundation Detection Results (HCI-CRS)

```
Foundation Modules (Total: 532)
├── database (441 refs)      ─ DAL classes, DB connections
├── security (91 refs)       ─ Authentication, authorization
├── logging (0 refs)         ─ Minimal logging
├── caching (0 refs)         ─ No caching layer
├── config (0 refs)          ─ Hardcoded config
└── utilities (0 refs)       ─ Inline utilities

Implicaties voor Migratie:
→ DAL moet volledig herschreven (ADODB → EF Core / Django ORM)
→ Security requires modernization (ASP.NET Identity / Django Auth)
→ Logging moet toegevoegd (Serilog / Django logging)
→ Caching architecture nodig (Redis/MemoryCache)
→ Config naar environment variables / appsettings
```

### 3.3 Planned Services (Week 130+) 📋

| Service | Agent | Priority | Description |
|---------|-------|----------|-------------|
| **LibraryInventoryService** | Felix | P0 - HIGH | External library inventory + mapping |
| **APIInventoryService** | Felix | P1 | Endpoint catalogus (internal + external) |
| **BusinessInventoryService** | Peter | P1 | Business rules, validations, calculations |
| **StateFlowService** | Felix | P2 | State machines, workflow patterns |

---

## 4. Library Mapping (HIGH RISK)

### 4.1 Risk Assessment

External libraries zijn een **HIGH RISK** item omdat ze niet 1:1 mappen tussen stacks.

### 4.2 Known Library Mappings

| Legacy (VB.NET) | .NET 8/Blazor | Django/React | Risk | Notes |
|-----------------|---------------|--------------|------|-------|
| **ADODB.Recordset** | EF Core DbContext | Django QuerySet | 🟡 Medium | Query rewrite needed |
| **ADODB.Connection** | DbContext + DI | Django connection | 🟡 Medium | Connection management differs |
| **Microsoft.Office.Interop.Excel** | ClosedXML | openpyxl | 🟢 Low | Similar API concepts |
| **MSXML2.XMLHTTP** | HttpClient | requests/aiohttp | 🟢 Low | Modern HTTP clients |
| **Crystal Reports** | RDLC / FastReport | ReportLab / WeasyPrint | 🔴 High | Complete rewrite |
| **WeSeesDo Integration** | Custom HTTP client | Custom HTTP client | 🟡 Medium | API wrapper needed |

### 4.3 LibraryInventoryService Design (Full Scope)

```python
@dataclass
class LibraryReference:
    """Individual library reference found in codebase."""
    name: str                     # "ADODB"
    version: Optional[str]        # "2.8"
    reference_type: str           # "COM", "Assembly", "NuGet", "DLL"
    file_path: str                # Where it's referenced
    usage_count: int              # Number of references
    usage_patterns: List[str]     # ["Recordset", "Connection", "Command"]


@dataclass
class TransitiveDependency:
    """Dependency of a dependency."""
    parent_library: str           # "EntityFramework"
    child_library: str            # "System.Data.SqlClient"
    version: str                  # "4.8.0"
    depth: int                    # 1 = direct, 2+ = transitive


@dataclass
class SecurityVulnerability:
    """Known vulnerability in a library."""
    cve_id: str                   # "CVE-2024-12345"
    severity: str                 # "critical", "high", "medium", "low"
    affected_versions: str        # "<= 2.8.0"
    fixed_version: Optional[str]  # "2.9.0"
    description: str              # Vulnerability description
    remediation: str              # How to fix


@dataclass
class LicenseInfo:
    """License information for compliance."""
    license_type: str             # "MIT", "GPL", "Proprietary"
    commercial_use: bool          # Allowed for commercial?
    attribution_required: bool    # Must include attribution?
    license_url: Optional[str]    # Link to full license


@dataclass
class LibraryMapping:
    """Complete library mapping with Full scope."""
    # Legacy info
    legacy_library: str           # "ADODB"
    legacy_version: Optional[str] # "2.8"
    reference_type: str           # "COM", "Assembly", "NuGet", "DLL"
    usage_count: int              # Aantal referenties in codebase
    usage_patterns: List[str]     # ["Recordset", "Connection", "Command"]
    usage_locations: List[str]    # File paths where used

    # Stack A mappings (.NET 8)
    dotnet_equivalent: Optional[str]      # "Entity Framework Core 8"
    dotnet_version: Optional[str]         # "8.0.0"
    dotnet_migration_effort: str          # "low", "medium", "high", "critical"
    dotnet_notes: str                     # Implementation notes
    dotnet_code_changes: List[str]        # Required code changes

    # Stack B mappings (Python/Django)
    python_equivalent: Optional[str]      # "Django ORM"
    python_version: Optional[str]         # "5.1"
    python_migration_effort: str          # "low", "medium", "high", "critical"
    python_notes: str                     # Implementation notes
    python_code_changes: List[str]        # Required code changes

    # Risk assessment
    risk_level: str               # "low", "medium", "high", "critical"
    requires_rewrite: bool        # True if no direct equivalent
    breaking_changes: List[str]   # API differences to handle

    # Transitive dependencies
    transitive_deps: List[TransitiveDependency]

    # Security
    vulnerabilities: List[SecurityVulnerability]
    security_score: int           # 0-100

    # License
    license_info: Optional[LicenseInfo]
    license_compatible: bool      # Compatible with project license?


@dataclass
class LibraryInventoryReport:
    """Complete inventory report."""
    scan_date: datetime
    source_path: str
    total_libraries: int
    by_type: Dict[str, int]       # {"COM": 5, "Assembly": 12, ...}

    # All mappings
    mappings: List[LibraryMapping]

    # Risk summary
    critical_risk_count: int
    high_risk_count: int
    security_issues_count: int
    license_issues_count: int

    # Recommendations
    recommendations: List[str]
    estimated_effort_hours: float
```

---

## 5. Evaluation Criteria

### 5.1 Weighted Scoring Matrix

| Criterium | Gewicht | Stack A (.NET) | Stack B (Django) | Hoe te Meten |
|-----------|---------|----------------|------------------|--------------|
| **Developer Experience** | 20% | - | - | Team survey, IDE support |
| **Performance** | 20% | - | - | Response times, throughput |
| **Test Coverage** | 15% | - | - | Unit/integration/E2E % |
| **Code Quality** | 15% | - | - | SonarQube, linting |
| **UI Fidelity** | 15% | - | - | Pixel comparison, UX test |
| **Deployment Complexity** | 10% | - | - | CI/CD setup, containers |
| **Maintainability** | 5% | - | - | Cyclomatic complexity |

### 5.2 Evaluation Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EVALUATION WORKFLOW                                                         │
│                                                                              │
│  1. PARALLEL DEVELOPMENT                                                     │
│     ├── Stack A team: .NET 8 + Blazor implementatie                         │
│     └── Stack B team: Django + React implementatie                          │
│                                                                              │
│  2. MILESTONE CHECKPOINTS                                                    │
│     ├── M1: Foundation modules complete (DAL, Auth)                         │
│     ├── M2: Core business logic complete                                    │
│     ├── M3: UI complete (pixel-perfect)                                     │
│     └── M4: Full integration + tests                                        │
│                                                                              │
│  3. SCORING AT EACH MILESTONE                                                │
│     ├── Run automated metrics (tests, coverage, performance)                │
│     ├── Conduct code review (quality, maintainability)                      │
│     └── UI comparison test (visual regression)                              │
│                                                                              │
│  4. FINAL DECISION                                                           │
│     ├── Calculate weighted scores                                           │
│     ├── Review qualitative factors                                          │
│     └── Select winning stack for production                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Migration Order

### 6.1 Recommended Sequence

Beide stacks volgen dezelfde migratie volgorde:

```
Phase 1: Foundation (Week 1-2)
├── Database models / entities
├── Authentication / authorization
├── Configuration management
└── Logging infrastructure

Phase 2: DAL → Modern ORM (Week 3-4)
├── 12 DAL classes → EF Core / Django models
├── Connection management
├── Transaction handling
└── Query optimization

Phase 3: BLL → Services (Week 5-6)
├── 12 BLL managers → Service classes
├── Business validation rules
├── WeSeesDo integration adapter
└── Error handling

Phase 4: UI → Modern Frontend (Week 7-8)
├── 8 ASPX pages → Blazor/React components
├── Form validation
├── State management
└── API integration

Phase 5: Testing & Validation (Week 9-10)
├── Unit tests (80%+ coverage target)
├── Integration tests
├── E2E tests (Playwright)
└── Visual regression tests
```

### 6.2 Module Priority

| Module | Priority | Dependencies | LOC | Complexity |
|--------|----------|--------------|-----|------------|
| **AfspraakEntity** | P0 | None | ~500 | Low |
| **AfspraakDAL** | P0 | Entity | ~800 | Medium |
| **AfspraakBLL** | P1 | DAL | ~1200 | High |
| **AfspraakWeb** | P2 | BLL | ~600 | Medium |
| **WeSeesDoAdapter** | P1 | None | ~400 | Medium |
| **ReportingModule** | P3 | All | ~300 | Low |

---

## 7. Document Generation

### 7.1 Auto-Generated vs Hand-Written

| Aspect | Auto-Generated | Hand-Written | Recommendation |
|--------|----------------|--------------|----------------|
| **Project Overview** | ✅ MigrationPlan.to_markdown() | Context, nuances | Hybrid |
| **Technology Stack** | ✅ target_stacks field | Architectuur diagrammen | Hybrid |
| **Foundation Analysis** | ✅ foundation_summary | Module volgorde | Hybrid |
| **Estimation** | ✅ Eliza agent (FP/SP) | - | Auto |
| **Risks** | ✅ Template | Project-specifiek | Hybrid |
| **Setup Commands** | ❌ Not supported | ✅ Required | Hand-written |
| **Epic/Story Structure** | ❌ Via HierarchicalExtraction | ✅ INVEST criteria | Hand-written |

### 7.2 Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT GENERATION STRATEGY                                                │
│                                                                              │
│  1. BASE: MigrationPlan.to_markdown()                                        │
│     └── Automatically generated from database model                         │
│                                                                              │
│  2. ENRICHMENT: Hand-written additions                                       │
│     ├── ASCII architecture diagrams                                         │
│     ├── Setup commands (bash, docker)                                       │
│     ├── Project-specific context                                            │
│     └── Decision rationale                                                  │
│                                                                              │
│  3. SYNC: On model update                                                    │
│     ├── Regenerate base document                                            │
│     ├── Preserve hand-written sections                                      │
│     └── Detect and resolve conflicts                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Status

### 8.1 Completed (Week 128-129) ✅

| Component | File | Description |
|-----------|------|-------------|
| **MigrationPlan Extensions** | `backend/app/models/project_assessment.py` | 12 new fields |
| **Database Migration** | `backend/alembic/versions/059_*.py` | Dual-stack columns |
| **Format Comparison** | `docs/architecture/migration-plan-format-comparison.md` | Hand vs Auto |
| **Brown Paper Enhanced** | `backend/app/services/brown_paper_service.py` | 6-phase analysis |
| **Foundation Detection** | Integration in BROWN_PAPER_ENHANCED | Module categorization |

### 8.2 In Progress (Week 129)

| Task | Status | Notes |
|------|--------|-------|
| AGENTS.md update | ✅ Done | Dual-stack + extraction sections |
| ROADMAP.md update | ✅ Done | Week 129 progress |
| PROJECT_STATUS_SUMMARY.md update | ✅ Done | New metrics |
| README.md update | ✅ Done | Migration capabilities |
| Comprehensive migration doc | ✅ This document | - |

### 8.3 Planned (Week 130+)

| Service | Priority | Description |
|---------|----------|-------------|
| LibraryInventoryService | P0 | External library mapping |
| APIInventoryService | P1 | Endpoint catalogus |
| BusinessInventoryService | P1 | Business rules extraction |
| Setup commands generation | P2 | Auto-generate from target_stacks |

---

## 9. Beslissingen (Beantwoord 2025-12-31)

### 9.1 LibraryInventoryService Scope ✅ BESLOTEN

**Beslissing:** Optie D - **FULL SCOPE**

| Component | Include | Beschrijving |
|-----------|---------|--------------|
| **COM/ActiveX** | ✅ | ADODB, MSXML, Office Interop |
| **Assembly References** | ✅ | .NET Framework references |
| **NuGet Packages** | ✅ | Geïnstalleerde packages |
| **Third-party DLLs** | ✅ | Externe DLLs in bin/ |
| **License Info** | ✅ | License compliance check |
| **Transitive Dependencies** | ✅ | Dependencies van dependencies |
| **Security Audit** | ✅ | Known vulnerabilities (CVE check) |

### 9.2 API Extraction Scope ✅ BESLOTEN

**Beslissing:** **ALLE APIs** catalogiseren

| Type | Include | Beschrijving |
|------|---------|--------------|
| **Internal APIs** | ✅ | Interne service calls tussen modules |
| **External APIs** | ✅ | WeSeesDo, andere externe integrations |
| **Stored Procedures** | ✅ | Database APIs (24 SQL files) |
| **File System** | ✅ | File I/O operaties |

### 9.3 Business Functionality Extraction ✅ BESLOTEN

**Beslissing:** **ALLE functionaliteit tot op het diepste detail**

| Category | Include | Extraction Depth |
|----------|---------|------------------|
| **Workflows** | ✅ | Volledige state machines, alle transities |
| **Events** | ✅ | Triggers, notifications, callbacks |
| **Validations** | ✅ | Alle business rules, constraints, error messages |
| **Calculations** | ✅ | Algoritmes, formules, pricing logic |
| **Edge Cases** | ✅ | Exception handling, fallback logic |
| **Data Transformations** | ✅ | Mapping, conversies, formatting |

### 9.4 HCI-CRS Specific Decisions ✅ BESLOTEN

| # | Vraag | Beslissing | Actie |
|---|-------|------------|-------|
| 1 | Classic ASP migreren? | ✅ **JA** | Include in migration scope |
| 2 | WeSeesDo in gebruik? | ✅ **JA** | Create integration adapter |
| 3 | Background jobs? | 🔍 **ONDERZOEKEN** | Added to roadmap Week 130 |
| 4 | Verwachte load? | 🔍 **ONDERZOEKEN** | Added to roadmap Week 130 |
| 5 | Business rules docs? | 🔍 **ONDERZOEKEN** | Extract from code analysis |

### 9.5 Technical Decisions ✅ BESLOTEN

| # | Beslissing | Keuze | Rationale |
|---|------------|-------|-----------|
| 1 | Blazor render mode | **Te bepalen per component** | Hybrid approach mogelijk |
| 2 | React state management | **Te bepalen** | Redux vs Zustand evaluatie |
| 3 | Test framework | **xUnit (.NET) / pytest (Python)** | Industry standard |
| 4 | CI/CD platform | **Aparte pipelines per stack** | Onafhankelijk deployment |
| 5 | Hosting | **Te bepalen** | Azure vs AWS evaluatie |

### 9.6 CI/CD Strategy ✅ BESLOTEN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DUAL CI/CD PIPELINES                                                        │
│                                                                              │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐         │
│  │  STACK A: .NET 8/Blazor     │    │  STACK B: Django/React      │         │
│  ├─────────────────────────────┤    ├─────────────────────────────┤         │
│  │ Pipeline: stack-a.yml       │    │ Pipeline: stack-b.yml       │         │
│  │ ├── Build (.NET SDK 8)      │    │ ├── Build (Python 3.12)     │         │
│  │ ├── Test (xUnit)            │    │ ├── Test (pytest)           │         │
│  │ ├── Lint (dotnet format)    │    │ ├── Lint (ruff, black)      │         │
│  │ ├── Security (Snyk)         │    │ ├── Security (Bandit, Snyk) │         │
│  │ ├── Docker build            │    │ ├── Docker build            │         │
│  │ └── Deploy to staging       │    │ └── Deploy to staging       │         │
│  └─────────────────────────────┘    └─────────────────────────────┘         │
│                                                                              │
│  INDEPENDENT DEPLOYMENT:                                                     │
│  - Stack A kan deployen zonder Stack B                                      │
│  - Stack B kan deployen zonder Stack A                                      │
│  - Shared database migraties apart beheerd                                  │
│  - Feature flags voor stack switching                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Next Steps

### Immediate (Week 130)

1. [ ] Run database migration `059_add_migration_plan_dual_stack_fields.py`
2. [x] Answer open questions (Section 9) ✅ DONE
3. [ ] Start LibraryInventoryService implementation (FULL scope)
4. [ ] Create project structures for both stacks
5. [ ] Set up CI/CD pipelines (stack-a.yml + stack-b.yml)
6. [ ] 🔍 Onderzoek: HCI-CRS background jobs / scheduled tasks
7. [ ] 🔍 Onderzoek: Verwachte load (users/requests)

### Short-term (Week 131-132)

1. [ ] Complete LibraryInventoryService (with CVE check, license info)
2. [ ] Implement APIInventoryService (internal + external + stored procs)
3. [ ] Implement BusinessInventoryService (workflows, validations, calculations)
4. [ ] Start Phase 1 development (Foundation) for both stacks
5. [ ] First milestone checkpoint

### Medium-term (Week 133-140)

1. [ ] Complete dual-stack development (parallel)
2. [ ] Run evaluation at each milestone (7 criteria)
3. [ ] Final stack comparison
4. [ ] Production deployment decision

### Classic ASP Migration (Added)

1. [ ] Inventory 4 Classic ASP pages
2. [ ] Determine migration strategy per page
3. [ ] Include in Phase 4 (UI migration)

### WeSeesDo Integration (Added)

1. [ ] Document current API usage
2. [ ] Create adapter interface
3. [ ] Implement for both stacks (HttpClient / requests)

---

## 11. Related Documents

| Document | Description |
|----------|-------------|
| [hci-crs-migration-plan.md](hci-crs-migration-plan.md) | Project-specific migration plan |
| [migration-plan-format-comparison.md](migration-plan-format-comparison.md) | Auto vs Hand comparison |
| [brown-paper-enhanced.md](brown-paper-enhanced.md) | 6-phase analysis specification |
| [migration-enhanced.md](migration-enhanced.md) | 7-phase execution specification |
| [AGENTS.md](../../AGENTS.md) | Agent system reference |
| [quality-assessment-cicd.md](quality-assessment-cicd.md) | Quality CI/CD pipelines for dual-stack comparison |
| [ROADMAP.md](../../ROADMAP.md) | Project timeline |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Author:** Claude Code Agent + User Collaboration
