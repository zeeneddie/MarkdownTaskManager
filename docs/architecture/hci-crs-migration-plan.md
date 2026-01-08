# HCI-CRS Migratie Plan

**Datum:** 2025-12-31
**Status:** IN PROGRESS
**Aanpak:** Dual-Migration - Parallelle evaluatie .NET/Blazor vs Python Django/React
**Doel:** Evaluatie welke stack beste fit is voor HCI-CRS

---

## 1. Analyse Resultaten

### 1.1 Totaal Scope

| Metric | Waarde |
|--------|--------|
| Totaal modules | 84 |
| Totaal bestanden | 4.223 |
| Totaal LOC | 793.962 |
| Dependencies | 16.444 |
| Circular dependencies | 3 (false positives) |

### 1.2 Technologie Stack

**Bron (Legacy):**
- ASP Classic (VBScript)
- ASP.NET WebForms (.aspx/.vb)
- SQL Server
- COM Components (ADODB, etc.)

**Doel Stack A: .NET/Blazor**
- Blazor Server (.NET 8 LTS)
- Entity Framework Core (ORM)
- SQL Server (bestaand schema behouden)
- xUnit + bUnit (test framework)

**Doel Stack B: Python Django/React**
- Django 5.x (Python 3.12)
- Django ORM
- SQL Server (bestaand schema behouden, pyodbc/mssql-django)
- React 18 (TypeScript) frontend
- pytest + React Testing Library (test framework)

**Gedeeld:**
- SQL Server database (geen schema wijzigingen)
- Legacy UI als referentie (screenshots/specs)
- Business rules uit BROWN_PAPER_ENHANCED extractie

### 1.3 Dependency Analyse

Uitgevoerd met `DependencyGraphService` (uitgebreid met ASP Classic support).

**Meest afhankelijke modules (Foundation):**

| Module | References | Functie |
|--------|------------|---------|
| `Procedures/Security` | 2.818 | Auth, permissions |
| `Includes/Footer` | 1.432 | UI layout |
| `Procedures/HTMLFormElements` | 1.241 | Form components |
| `Procedures/DatabaseHandling` | 1.231 | DB operations |
| `Procedures/StandardReportCode` | 805 | Reporting |
| `Procedures/StandardFormCode` | 746 | Form CRUD |
| `Includes/HeaderMenu` | 698 | Navigation |
| `Procedures/StandardListCode` | 435 | List views |
| `Procedures/StandardSearchCode` | 388 | Search |

---

## 2. Migratie Strategie

### 2.1 Gekozen Aanpak: Dual-Migration (Parallelle Evaluatie)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BROWN_PAPER_ENHANCED (Shared)                         │
│  ├── Foundation Detection (1.681 modules)                                   │
│  ├── Business Rules Extractie                                               │
│  ├── Legacy UI Screenshots/Specs (referentie)                               │
│  └── Database Schema Analyse                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   STACK A: .NET/Blazor       │         │   STACK B: Django/React      │
│                              │         │                              │
│  FASE 0: FOUNDATION          │  SYNC   │  FASE 0: FOUNDATION          │
│  ├── EF Core DAL             │◄───────►│  ├── Django ORM DAL          │
│  ├── Blazor Components       │         │  ├── React Components        │
│  ├── Auth (ASP.NET Identity) │         │  ├── Auth (Django Auth)      │
│  └── xUnit tests             │         │  └── pytest tests            │
│                              │         │                              │
│  FASE 1-3: BUSINESS          │  SYNC   │  FASE 1-3: BUSINESS          │
│  (zelfde volgorde)           │◄───────►│  (zelfde volgorde)           │
└──────────────────────────────┘         └──────────────────────────────┘
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVALUATIE CHECKPOINT                                 │
│  Na elke fase: vergelijk beide stacks op evaluatiecriteria                  │
│  Eindkeuze: na FASE 1 (Core Business) of FASE 2 (Extended)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Fase Inhoud (identiek voor beide stacks):**

| Fase | Scope | LOC |
|------|-------|-----|
| FASE 0: Foundation | Admin, Security, Database Layer, UI Components, Shared Services | ~230K |
| FASE 1: Core Business | Login, Client/Patient, Dossier (basis), Afspraken/Agenda | ~75K |
| FASE 2: Extended Business | Financieel, Declaraties, Berichten (iWMO, iJW, AZR), ROM, ZPM | ~150K |
| FASE 3: Reporting & Legacy | Output/Reports, Tabellen, Overige legacy | ~340K |

### 2.2 Module Volgorde (Dependency-based)

**Standalone modules eerst (minste dependencies):**

| # | Module | LOC | Dependencies | Reden |
|---|--------|-----|--------------|-------|
| 1 | SessionShare | 52 | 0 | Geen deps |
| 2 | Mobiel | 985 | 1 | Bijna standalone |
| 3 | Login | 2.285 | 2 | Core auth |
| 4 | Validate | 4.572 | 2 | Shared validation |
| 5 | Client | 7.000 | 3 | Core entity |
| 6 | Afspraken | 3.099 | 3 | Core business |
| 7 | Agenda2 | 5.784 | 3 | Scheduling |
| 8 | Dossier | 58.266 | 4 | Core business |
| 9 | Financieel | 22.438 | 4 | Business |
| 10 | ROM | 2.446 | 3 | Clinical |

---

## 3. Kanban Structuur

### 3.1 Epic Breakdown

```
EPIC 0: Foundation Infrastructure
├── FEATURE 0.1: Security & Auth
├── FEATURE 0.2: Database Layer
├── FEATURE 0.3: Blazor UI Components
└── FEATURE 0.4: Shared Services

EPIC 1: Login & Session Management
├── FEATURE 1.1: User Authentication
├── FEATURE 1.2: Session Handling
├── FEATURE 1.3: Permission System
└── FEATURE 1.4: UZI Integration

EPIC 2: Client/Patient Management
├── FEATURE 2.1: Client CRUD
├── FEATURE 2.2: Client Search
├── FEATURE 2.3: Client History
└── FEATURE 2.4: Contactpersonen

EPIC 3: Dossier Management
├── FEATURE 3.1: Dossier CRUD
├── FEATURE 3.2: Dossier Documents
├── FEATURE 3.3: Dossier History
└── FEATURE 3.4: Dossier Sharing

EPIC 4: Afspraken/Agenda
├── FEATURE 4.1: Agenda Views (dag/week/maand)
├── FEATURE 4.2: Afspraak CRUD
├── FEATURE 4.3: Hulpverlener Management
├── FEATURE 4.4: WeSeesDo Integration
└── FEATURE 4.5: Batch Operations
```

### 3.2 Story Sizing Rules

Gebaseerd op bestaande INVEST criteria:

| Criterium | Regel |
|-----------|-------|
| **Independent** | Story moet onafhankelijk deploybaar zijn |
| **Negotiable** | Scope kan bijgesteld worden |
| **Valuable** | Levert waarde voor eindgebruiker |
| **Estimable** | Max 1 dag werk (4-8 uur BUILD) |
| **Small** | Single dev agent completion |
| **Testable** | Heeft duidelijke acceptance criteria |

**Task breakdown:**
- Story = 4-8 uur totaal
- Task = 1-2 uur max
- Elke Story heeft 3-6 Tasks

### 3.3 Test Coverage Requirement (VERPLICHT)

```
┌─────────────────────────────────────────────────────────────────┐
│  TEST COVERAGE VEREISTEN                                        │
│                                                                 │
│  MINIMUM:  90% coverage per module/scherm/functie/object       │
│  DOEL:     100% coverage                                        │
│                                                                 │
│  GEEN UITZONDERINGEN - Code zonder tests wordt NIET gemerged   │
└─────────────────────────────────────────────────────────────────┘
```

**Test-First Development:**

| Wat | Test Type | Coverage |
|-----|-----------|----------|
| Business Rules | Unit Tests | 100% |
| Services | Unit + Integration | ≥90% |
| API Endpoints | Integration Tests | 100% |
| Blazor Components | Component Tests | ≥90% |
| Database Operations | Integration Tests | 100% |
| Edge Cases | Unit Tests | 100% |

**Definition of Done per Item:**

```
□ Code geschreven
□ Unit tests geschreven (coverage ≥90%)
□ Integration tests geschreven (waar van toepassing)
□ Alle tests GROEN
□ Code review passed
□ Coverage rapport gegenereerd
□ Coverage ≥90% bevestigd
```

**Test Tools (.NET 8):**

| Tool | Doel |
|------|------|
| xUnit | Unit testing framework |
| Moq | Mocking |
| FluentAssertions | Assertions |
| bUnit | Blazor component testing |
| Testcontainers | Integration tests met DB |
| Coverlet | Coverage reporting |
| ReportGenerator | Coverage HTML reports |

### 3.4 Voorbeeld Story Breakdown

```
STORY 4.2.1: Afspraak aanmaken (basis)
├── TASK: Create AfspraakCreateModel.cs + unit tests
├── TASK: Create AfspraakService.CreateAsync() + unit tests
├── TASK: Create AfspraakCreate.razor component + bUnit tests
├── TASK: Add validation rules + unit tests
├── TASK: Write integration tests (DB)
└── TASK: Verify coverage ≥90%

Acceptance Criteria:
- [ ] Gebruiker kan nieuwe afspraak aanmaken
- [ ] Datum/tijd selectie werkt
- [ ] Hulpverlener selectie werkt
- [ ] Client selectie werkt
- [ ] Validatie toont errors
- [ ] Afspraak wordt opgeslagen in DB
- [ ] Unit test coverage ≥90%
- [ ] Integration tests GROEN
```

---

## 4. Foundation Componenten (Dual-Stack)

### 4.1 Te Bouwen Foundation (beide stacks)

| Component | ASP Classic | Stack A: .NET/Blazor | Stack B: Django/React |
|-----------|-------------|---------------------|----------------------|
| Security.asp | Permission checks | `IAuthorizationService` + Policies | Django Permissions + DRF |
| DatabaseHandling.asp | ADODB operations | Entity Framework Core | Django ORM |
| HTMLFormElements.asp | Form HTML generation | Blazor Components | React Components |
| StandardFormCode.asp | CRUD templates | Generic Repository + Blazor | Django ModelViewSet + React |
| StandardListCode.asp | List pages | Blazor DataGrid | React DataGrid (AG-Grid) |
| StandardSearchCode.asp | Search pages | Blazor Search Component | React Search + DRF filters |
| HeaderMenu.asp | Navigation | Blazor NavMenu | React Router + NavBar |
| Footer.asp | Page footer | Blazor MainLayout | React Layout Component |

### 4.2 Project Structuur Stack A (.NET/Blazor)

```
HciCrs.Blazor/
├── HciCrs.Domain/           # Entities, Value Objects
│   ├── Entities/
│   ├── ValueObjects/
│   └── Interfaces/
├── HciCrs.Application/      # Use Cases, Services
│   ├── Services/
│   ├── DTOs/
│   └── Interfaces/
├── HciCrs.Infrastructure/   # EF Core, External Services
│   ├── Data/
│   ├── Repositories/
│   └── Services/
├── HciCrs.Web/              # Blazor Server
│   ├── Components/
│   │   ├── Shared/          # Layout, NavMenu, etc.
│   │   ├── Forms/           # Generic form components
│   │   └── Pages/           # Feature pages
│   ├── Services/
│   └── wwwroot/
└── HciCrs.Tests/
    ├── Unit/
    └── Integration/
```

### 4.3 Project Structuur Stack B (Django/React)

```
hci-crs-django/
├── backend/                  # Django API
│   ├── hcicrs/              # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── core/            # Shared models, auth
│   │   ├── client/          # Client/Patient app
│   │   ├── dossier/         # Dossier app
│   │   ├── afspraken/       # Agenda/Appointments app
│   │   └── financieel/      # Financial app
│   ├── api/                 # Django REST Framework
│   │   ├── serializers/
│   │   └── views/
│   └── tests/               # pytest tests
│       ├── unit/
│       └── integration/
│
└── frontend/                 # React frontend
    ├── src/
    │   ├── components/      # Shared components
    │   │   ├── Layout/
    │   │   ├── Forms/
    │   │   └── DataGrid/
    │   ├── pages/           # Feature pages
    │   ├── services/        # API clients
    │   ├── hooks/           # Custom hooks
    │   └── types/           # TypeScript types
    └── tests/               # React Testing Library
```

### 4.4 Evaluatie Criteria

Na elke fase worden beide stacks vergeleken op:

| Criterium | Gewicht | Meetbaar Via |
|-----------|---------|--------------|
| **Developer Experience** | 20% | Team feedback survey (1-10) |
| **Performance** | 20% | Response time, memory, throughput |
| **Test Coverage** | 15% | Coverage % (doel: ≥90%) |
| **Code Quality** | 15% | SonarQube/linting scores |
| **UI Fidelity** | 15% | Visual regression vs legacy (% match) |
| **Deployment Complexity** | 10% | Steps, dependencies, config effort |
| **Maintainability** | 5% | Cyclomatic complexity, coupling |

**Beslismoment:**
- Na FASE 1 (Core Business): Preliminaire evaluatie
- Na FASE 2 (Extended Business): Definitieve keuze
- Winner gaat door naar FASE 3, verliezer wordt gearchiveerd

---

## 5. Business Rule Extractie

### 5.1 Reeds Uitgevoerd

Afspraak module geanalyseerd met `ClassicASPExtractor`:
- 99 business rules geëxtraheerd
- Rule types: validation, authorization, scheduling, workflow, branching

### 5.2 Te Extraheren per Module

| Module | Geschatte Rules | Status |
|--------|-----------------|--------|
| Afspraken | 99 | DONE |
| Login | ~50 | TODO |
| Client | ~150 | TODO |
| Dossier | ~300 | TODO |
| Financieel | ~200 | TODO |

### 5.3 Extractie Workflow

```
1. Run ClassicASPExtractor op module
2. Review business rules
3. Categoriseer per type (validation, auth, workflow)
4. Map naar .NET implementation
5. Write unit tests voor elke rule
```

---

## 6. Database Strategie

### 6.1 Beslissing: Bestaand Schema Behouden

- Geen schema migratie
- EF Core DbContext mappen op bestaande tabellen
- Stored procedures blijven (indien aanwezig)
- Views blijven

### 6.2 Key Tables (Afspraak Module)

```sql
-- Geïdentificeerd uit business rule extractie
taAfspraak              -- Hoofdtabel afspraken
taAfspraakHulpverlener  -- Koppeltabel
taAfsprakenFiatteringsLog
CRSHulpverlener         -- Medewerkers
Locatie                 -- Locaties
taStatusAgendaNietBeschikbaar
```

---

## 7. Generieke Migratieaanpak

### 7.1 Herbruikbaar voor Andere Applicaties

Deze aanpak is generiek en kan worden toegepast op:
- Andere ASP Classic applicaties
- PHP legacy applicaties
- Java legacy applicaties

### 7.2 Stappen per Legacy Applicatie

```
STAP 1: ANALYSE
├── Run DependencyGraphService
├── Identificeer foundation modules (meest afhankelijk)
├── Identificeer business modules (minste deps eerst)
└── Bereken LOC per module

STAP 2: BUSINESS RULE EXTRACTIE
├── Run juiste extractor (ASP/PHP/Java)
├── Categoriseer rules
├── Valideer met stakeholders
└── Documenteer in stories

STAP 3: FOUNDATION BOUWEN
├── Security/Auth layer
├── Database layer (EF Core of equivalent)
├── UI component library
└── Shared services

STAP 4: VERTICALE MIGRATIE
├── Per module: DB → Service → UI → Test
├── Business rules als unit tests
├── Integration tests per module
└── UAT per module

STAP 5: CUTOVER
├── Data sync strategy
├── Feature flags
├── Rollback plan
└── Go-live
```

### 7.3 Platform Tools Beschikbaar

| Tool | Functie | Locatie |
|------|---------|---------|
| DependencyGraphService | Module dependency analyse | `app/services/dependency_graph_service.py` |
| **FoundationDetectionService** | Foundation vs Business module classificatie | `app/services/foundation_detection_service.py` |
| ClassicASPExtractor | ASP business rule extractie | `app/services/static_analysis/classic_asp_extractor.py` |
| VBNetExtractor | VB.NET extractie | `app/services/static_analysis/vbnet_extractor.py` |
| ASPXExtractor | ASPX extractie | `app/services/static_analysis/aspx_extractor.py` |
| BrownPaperService | Legacy analyse workflow | `app/services/brown_paper_service.py` |
| HierarchicalStoryExtraction | Story generatie | `app/services/hierarchical_story_extraction_service.py` |

### 7.4 FoundationDetectionService Output (HCI-CRS)

De FoundationDetectionService heeft voor HCI-CRS de volgende classificatie gemaakt:

```
FOUNDATION MODULES: 1,681 (38.9%)
├── database:        441 modules (DB access patterns, SQL, stored procs)
├── admin:           474 modules (Admin panels, config management)
├── infrastructure:  427 modules (Logging, utilities, shared libs)
├── ui_components:   133 modules (Shared UI controls, templates)
├── shared_services: 115 modules (Cross-cutting concerns)
└── security:         91 modules (Auth, session, permissions)

BUSINESS MODULES: 2,642 (61.1%)
├── Afspraken/Agenda modules
├── Client/Patient modules
├── Dossier modules
├── Facturatie modules
└── Rapportage modules
```

**Migratie Implicatie:** Foundation modules moeten EERST gemigreerd worden naar BEIDE stacks voordat business modules kunnen starten.

---

## 8. Volgende Stappen (Dual-Stack Approach)

### 8.1 Dag 1: Project Setup

```
PARALLELLE SETUP
├── Stack A: .NET 8 / Blazor
│   ├── [ ] dotnet new blazorserver -n HciCrs.Blazor
│   ├── [ ] EF Core scaffolding (hci-crs database)
│   ├── [ ] Project structure conform 4.2
│   └── [ ] xUnit + bUnit test setup
│
└── Stack B: Django / React
    ├── [ ] django-admin startproject hci_crs
    ├── [ ] Django ORM models (inspectdb)
    ├── [ ] Create React app (Vite + TypeScript)
    └── [ ] pytest + React Testing Library setup
```

### 8.2 Week 1: Foundation Layer (Beide Stacks)

| Taak | Stack A (.NET/Blazor) | Stack B (Django/React) |
|------|----------------------|------------------------|
| Auth/Security | ASP.NET Identity + JWT | Django Auth + Simple JWT |
| Database Layer | EF Core DbContext | Django ORM Models |
| UI Components | Blazor Component Library | React Component Library |
| Shared Services | .NET DI Services | Django Services + React Hooks |
| **Evaluatie Punt** | Response times, dev experience | Response times, dev experience |

### 8.3 Week 2: Login Module (Eerste Vergelijkbare Feature)

1. [ ] Login UI exact conform legacy screenshots
2. [ ] Session management
3. [ ] Role-based access
4. [ ] **Vergelijk:** Code kwaliteit, test coverage, performance

### 8.4 Milestone: Evaluation Decision

**Na Week 2:** Beslissingsmoment op basis van:

| Criterium | Gewicht | Stack A Score | Stack B Score |
|-----------|---------|---------------|---------------|
| Developer Experience | 20% | ___ / 10 | ___ / 10 |
| Performance (login flow) | 20% | ___ / 10 | ___ / 10 |
| Test Coverage | 15% | ___ / 10 | ___ / 10 |
| Code Quality (SonarQube) | 15% | ___ / 10 | ___ / 10 |
| UI Fidelity vs Legacy | 15% | ___ / 10 | ___ / 10 |
| Deployment Complexity | 10% | ___ / 10 | ___ / 10 |
| Maintainability | 5% | ___ / 10 | ___ / 10 |
| **TOTAAL** | 100% | ___ | ___ |

**Decision Options:**
- A) Verder met Stack A (.NET/Blazor)
- B) Verder met Stack B (Django/React)
- C) Hybrid: Bepaalde modules in Stack A, andere in Stack B
- D) Meer evaluatie nodig (nog 1 module parallel)

### 8.5 Milestone: MVP (Na Stack Keuze)

**Scope:** Login + Client + Afspraken + Dossier (basis)
**Geschatte LOC:** ~70K van 800K
**Definition of Done:**
- Alle business rules geïmplementeerd (gekozen stack)
- Unit test coverage > 80%
- Integration tests passing
- UAT goedgekeurd
- Performance baseline ≤ 110% van legacy

---

## 9. Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Ongedocumenteerde business rules | Hoog | LLM-assisted extractie + stakeholder review |
| Database schema complexiteit | Medium | ORM scaffolding (EF Core / Django inspectdb) |
| Performance degradatie | Medium | Performance tests per module, beide stacks |
| Scope creep | Hoog | Strikte fase-grenzen, MVP focus |
| **Dual-stack overhead** | Medium | Timeboxed evaluatie (2 weken), daarna keuze |
| **UI inconsistentie tussen stacks** | Medium | Legacy screenshots als single source of truth |
| **Verschillende ORM gedrag** | Laag | Zelfde database, integration tests valideren |
| **Team skills imbalance** | Medium | Pair programming, kennis delen tussen teams |

---

## 10. Appendix

### A. Analyse Commando's (MarQed.ai Platform)

```bash
# Dependency analyse
source .venv/bin/activate
python3 -c "
from app.services.dependency_graph_service import DependencyGraphService
service = DependencyGraphService()
result = service.analyze_directory('/opt/projecten/hci-crs/src/EPD/WEB')
"

# Foundation detection (NEW)
python3 -c "
from app.services.foundation_detection_service import FoundationDetectionService
service = FoundationDetectionService()
result = service.detect_foundations('/opt/projecten/hci-crs/src/EPD/WEB')
print(f'Foundation: {len(result.foundation_modules)}')
print(f'Business: {len(result.business_modules)}')
"

# Business rule extractie (Afspraak)
python3 -c "
from app.services.static_analysis.classic_asp_extractor import ClassicASPExtractor
extractor = ClassicASPExtractor()
rules = await extractor.extract_from_file('/opt/projecten/hci-crs/src/EPD/WEB/Afspraken/Agenda.asp')
"
```

### B. Stack A Setup (.NET 8 / Blazor)

```bash
# Project setup
dotnet new blazorserver -n HciCrs.Blazor -o /opt/projecten/hci-crs-blazor
cd /opt/projecten/hci-crs-blazor

# Database scaffolding (EF Core)
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package Microsoft.EntityFrameworkCore.Tools
dotnet ef dbcontext scaffold "Server=localhost;Database=hci-crs;..." Microsoft.EntityFrameworkCore.SqlServer -o Models

# Test setup
dotnet new xunit -n HciCrs.Tests
dotnet add package bunit
```

### C. Stack B Setup (Django / React)

```bash
# Django setup
python -m venv venv
source venv/bin/activate
pip install django djangorestframework django-cors-headers

django-admin startproject hci_crs /opt/projecten/hci-crs-django
cd /opt/projecten/hci-crs-django

# Database introspection (Django ORM)
python manage.py inspectdb > core/models.py

# React frontend setup
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install axios react-router-dom @tanstack/react-query

# Test setup
pip install pytest pytest-django pytest-asyncio
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

### D. Gerelateerde Documenten

- [AGENTS.md](../../AGENTS.md) - Agent system reference
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Platform architecture
- [brown-paper-enhanced.md](brown-paper-enhanced.md) - Legacy analysis workflow
- [migration-enhanced.md](migration-enhanced.md) - Migration execution workflow

---

**Auteur:** Claude (AI Agent)
**Review:** Pending
**Laatste update:** 2025-12-31
