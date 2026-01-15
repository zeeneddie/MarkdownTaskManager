# MarQed.ai Client Portal - Implementatie Roadmap

**Versie:** 1.0
**Datum:** 2026-01-15
**Status:** CONCEPT voor review
**Doelgroep:** Intern team + AI Agents

---

## Executive Summary

Dit document beschrijft de gedetailleerde implementatie roadmap voor het MarQed.ai Client Portal. De roadmap is gebaseerd op:
- **Huidige fase:** Week 157, Fase 24 Quick Wins (60% complete)
- **Bestaande services:** 221 services, ~180 actief
- **Test projecten:** HCI-CRS (418K LOC), FysioOne, FRM
- **Agents:** 11 AI agents beschikbaar

### Kernprincipes

1. **AI-First Development:** Alles wordt door AI agents gemaakt
2. **Klantwaarde Prioritering:** Features die klanten direct zien eerst
3. **Iteratief Testen:** 3 echte projecten als validatie
4. **Eat Our Own Dogfood:** MarQed zelf als klant op het platform

---

## 1. PRIORITEITEN OP BASIS VAN KLANTWAARDE

### 1.1 Must Work 100% (Launch Blockers)

Deze features MOETEN foutloos werken voor productie launch:

| Prioriteit | Feature | Waarom Kritisch | Afhankelijkheden |
|------------|---------|-----------------|------------------|
| **P1** | Multi-tenant isolatie | Security/data breach risico | PostgreSQL RLS, Django middleware |
| **P1** | Authenticatie & Autorisatie | Klant data toegang | JWT, rol-based access |
| **P1** | Klant login/dashboard | Eerste indruk | React + Refine |
| **P1** | Quickscan (Fase 24-A1) | Sales enablement | ✅ Al klaar |
| **P1** | FP Inschatting flow | Kernproduct | Eliza agent |
| **P1** | Kanban basic (9 lanes) | Workflow zichtbaarheid | WebSocket |
| **P1** | Agent activiteit zichtbaar | USP differentiator | Confucius events |

### 1.2 Should Work Well (Launch Week Fixes OK)

| Prioriteit | Feature | Tolerantie | Afhankelijkheden |
|------------|---------|------------|------------------|
| **P2** | Brown Paper workflow | Minor bugs OK | Miguel, Peter, Betty |
| **P2** | Green Paper workflow | Minor bugs OK | Peter, Betty, Felix |
| **P2** | FP Dashboard | UI polish later | D3.js visualisaties |
| **P2** | Comments systeem | Basic versie eerst | Threading later |
| **P2** | Notificaties (email) | Best effort | SMTP |

### 1.3 Nice to Have (Post-Launch)

| Prioriteit | Feature | Status | Timeline |
|------------|---------|--------|----------|
| **P3** | SSO (Azure AD/Google) | Design ready | Month 2 |
| **P3** | Attachments (file upload) | Design ready | Month 2 |
| **P3** | Offline Quickscan sync | Ontwerp fase | Month 3 |
| **P3** | Export multi-format | Fase 24-M1 | Week 170+ |
| **P3** | Jira/ServiceNow integratie | Fase 28 | Week 225+ |

---

## 2. IMPLEMENTATIE FASES

### Fase A: Foundation (Week 158-163) - 6 weken

**Doel:** Multi-tenant basis en authenticatie

```
Week 158-159: Multi-Tenant Infrastructure
├── Day 1-3: PostgreSQL Row-Level Security
│   ├── Tenant table met UUID
│   ├── RLS policies per tabel
│   └── 100% test coverage
│
├── Day 4-5: Django Middleware
│   ├── TenantMiddleware (subdomain extraction)
│   ├── tenant_id injection in alle queries
│   └── Integration tests
│
└── Day 6-10: Database Migration
    ├── Alembic migration voor tenant_id
    ├── Backfill existing data
    └── Validation scripts

Week 160-161: Authentication & Authorization
├── Day 1-3: JWT Implementation
│   ├── Login/logout endpoints
│   ├── Token refresh flow
│   ├── Multi-tenant token claims
│   └── 100% test coverage
│
├── Day 4-5: Role-Based Access Control
│   ├── User roles table
│   ├── Permission decorators
│   ├── Role hierarchy (Viewer → Admin)
│   └── Per-Epic/Feature rechten
│
└── Day 6-10: Django BFF Integration
    ├── Proxy endpoints
    ├── Session management
    └── CORS configuration

Week 162-163: Basic Frontend
├── Day 1-3: React + Refine Setup
│   ├── Project scaffold
│   ├── shadcn/ui components
│   ├── Tailwind CSS theming
│   └── MarQed brand styling
│
├── Day 4-7: Core Pages
│   ├── Login page
│   ├── Dashboard (project overview)
│   ├── Project detail page
│   └── Basic navigation
│
└── Day 8-10: Authentication Integration
    ├── JWT token handling
    ├── Protected routes
    └── Role-based rendering
```

**Test Criteria Fase A:**
- [ ] Tenant A kan NOOIT data van Tenant B zien
- [ ] Login werkt met JWT refresh
- [ ] Dashboard toont juiste projecten per tenant
- [ ] 100% test coverage op security code

---

### Fase B: Core Features (Week 164-171) - 8 weken

**Doel:** Kanban, FP flow, agent zichtbaarheid

```
Week 164-165: 9-Lane Kanban System
├── Day 1-5: Backend
│   ├── Lane state machine
│   ├── Quality gate integration
│   ├── WebSocket broadcast service
│   └── Confucius workflow hooks
│
└── Day 6-10: Frontend
    ├── Drag-drop Kanban board
    ├── Card component (status, agent, progress)
    ├── WebSocket connection
    └── Real-time updates

Week 166-167: FP Estimation Flow
├── Day 1-3: Backend Integration
│   ├── Connect Eliza agent
│   ├── FP calculation API
│   ├── Onderbouwing storage
│   └── Supervisor approval workflow
│
├── Day 4-7: Frontend
│   ├── FP detail component
│   ├── ILF/EIF/EI/EO/EQ breakdown
│   ├── Approval buttons
│   └── FP budget tracking
│
└── Day 8-10: Klant Zichtbaarheid
    ├── FP inschatting pagina
    ├── Historische inschattingen
    └── Budget verbruik grafiek

Week 168-169: Agent Activiteit Transparantie
├── Day 1-5: Event Streaming
│   ├── Confucius event webhook
│   ├── Agent activity log
│   ├── Progress calculation
│   └── WebSocket push
│
└── Day 6-10: Frontend
    ├── Agent avatar component
    ├── Activity feed
    ├── Progress bar per item
    └── "Agent aan het werk" indicator

Week 170-171: Brown Paper Integration
├── Day 1-5: Workflow API
│   ├── Start Brown Paper endpoint
│   ├── Stage progress tracking
│   ├── Output consolidation
│   └── Report generation
│
└── Day 6-10: Frontend
    ├── Brown Paper wizard
    ├── Stage progress view
    ├── Results dashboard
    └── PDF export
```

**Test Criteria Fase B:**
- [ ] Kanban kaarten schuiven real-time
- [ ] FP inschatting is leesbaar voor klant
- [ ] Agent activiteit is live zichtbaar
- [ ] Brown Paper workflow draait end-to-end

---

### Fase C: Workflow Completion (Week 172-179) - 8 weken

**Doel:** Green Paper, Migration, Quality workflows

```
Week 172-173: Green Paper Workflow
├── Day 1-3: 6-Question Wizard
│   ├── Question form component
│   ├── Answer validation
│   └── Session persistence
│
├── Day 4-7: Workflow Execution
│   ├── Connect Peter, Betty, Felix
│   ├── Constitution generation
│   ├── Spec generation
│   └── Epic/Feature/Story breakdown
│
└── Day 8-10: Output
    ├── Project structure viewer
    ├── FP totals
    └── Approval flow

Week 174-175: Migration Workflow
├── Day 1-5: 8-Question Migration Planning
│   ├── BMAD questions form
│   ├── Technical analysis (Miguel)
│   ├── Specification generation
│   └── Wave planning (Paul)
│
└── Day 6-10: Visualization
    ├── Migration roadmap view
    ├── Wave timeline
    ├── Risk indicators
    └── Effort breakdown

Week 176-177: Quality Workflow
├── Day 1-5: Quality Gate Integration
│   ├── Scan execution (Miguel)
│   ├── Metrics analysis
│   ├── Quality review (Quinn)
│   └── Remediation planning (Marcus)
│
└── Day 6-10: Dashboard
    ├── Quality metrics cards
    ├── Trend graphs
    ├── Issue list
    └── Remediation tracking

Week 178-179: Workflow Progress View (voor klant)
├── Day 1-5: Backend
│   ├── Simplified stage model
│   ├── Progress calculation
│   ├── ETA estimation
│   └── WebSocket events
│
└── Day 6-10: Frontend
    ├── Progress timeline component
    ├── Stage status indicators
    ├── Current agent display
    └── Estimated completion
```

**Test Criteria Fase C:**
- [ ] Green Paper produceert valide specs
- [ ] Migration workflow compleet met waves
- [ ] Quality gate blokkeert slechte code
- [ ] Klant ziet workflow voortgang

---

### Fase D: Polish & Launch Prep (Week 180-185) - 6 weken

**Doel:** Comments, notificaties, final testing

```
Week 180-181: Comments & Communication
├── Day 1-5: Comments Backend
│   ├── Comment model (threading)
│   ├── @mentions
│   ├── Supervisor ↔ Klant communicatie
│   └── Audit log
│
└── Day 6-10: Comments Frontend
    ├── Comment thread component
    ├── Markdown support
    ├── Notification badges
    └── Comment history

Week 182-183: Notifications System
├── Day 1-5: Email Notifications
│   ├── SendGrid integration
│   ├── Template management
│   ├── Preference settings
│   └── Unsubscribe handling
│
└── Day 6-10: In-App Notifications
    ├── Notification center
    ├── Real-time alerts
    ├── Mark as read
    └── Filter by type

Week 184-185: Launch Preparation
├── Day 1-5: Final Testing
│   ├── E2E test suite
│   ├── Load testing (concurrent users)
│   ├── Security audit
│   └── Accessibility check (WCAG)
│
└── Day 6-10: Documentation & Training
    ├── User documentation
    ├── Admin guide
    ├── Video tutorials
    └── Support playbook
```

**Test Criteria Fase D:**
- [ ] Comments threading werkt correct
- [ ] Email notificaties komen aan
- [ ] 50 concurrent users geen performance issues
- [ ] WCAG AA compliance

---

## 3. TEST PLANNING MET 3 PROJECTEN

### 3.1 Test Matrix

| Project | Type | LOC | Tech Stack | Test Focus |
|---------|------|-----|------------|------------|
| **HCI-CRS** | Legacy | 418K | Classic ASP | Brown Paper, Security, Quickscan |
| **FysioOne** | Healthcare | ~50K | PHP | Green Paper, GDPR compliance |
| **FRM** | Finance | ~100K | .NET | Migration, Quality gates |

### 3.2 HCI-CRS Test Plan

**Status:** Quickscan al gedraaid (NO_GO, 1569 person-months)

```
FASE A TEST (Week 163)
├── Multi-tenant: Maak HCI als eerste tenant
├── Login: Admin user voor HCI
└── Dashboard: HCI project zichtbaar

FASE B TEST (Week 171)
├── Brown Paper: Full workflow op HCI-CRS codebase
│   ├── Code Understanding (Miguel) - verwacht: 2421 files
│   ├── Domain Extraction - verwacht: ASP modules mapping
│   ├── Story Extraction - verwacht: 50+ stories
│   └── FP Estimation - verwacht: ~1500+ person-months
│
├── Kanban: Stories naar board
├── Agent Activity: Miguel, Peter zichtbaar
└── FP Flow: Inschatting voor 5 stories

FASE C TEST (Week 179)
├── Migration Workflow: HCI migration plan
│   ├── 8 vragen beantwoorden
│   ├── Wave planning (3 waves)
│   └── Risk assessment
│
└── Quality Workflow: Security scan
    ├── 288+ security findings (bekend)
    └── Remediaton planning
```

### 3.3 FysioOne Test Plan

```
FASE A TEST (Week 163)
├── Multi-tenant: FysioOne als tweede tenant
├── Rechten: Viewer vs Admin test
└── Isolatie: Kan FysioOne HCI data zien? (verwacht: NEE)

FASE B TEST (Week 171)
├── FP Inschatting: 3 nieuwe features
│   ├── Feature A: Patient registratie
│   ├── Feature B: Afspraak planning
│   └── Feature C: GDPR export
│
└── Kanban: Board met mixed states

FASE C TEST (Week 179)
├── Green Paper: Nieuwe module specificeren
│   ├── 6 vragen workflow
│   ├── Constitution output
│   └── Epic/Feature/Story breakdown
│
└── Quality: GDPR compliance check
```

### 3.4 FRM Test Plan

```
FASE A TEST (Week 163)
├── Multi-tenant: FRM als derde tenant
├── Rechten: Granulaire Epic/Feature rechten
└── Login: Meerdere users per tenant

FASE B TEST (Week 171)
├── Quality Workflow: Code quality scan
│   ├── Technical debt analysis
│   ├── Security vulnerabilities
│   └── Performance hotspots
│
└── FP Inschatting: Enhancement requests

FASE C TEST (Week 179)
├── Migration Workflow: .NET upgrade plan
│   ├── .NET Framework → .NET 8
│   ├── Dependency analysis
│   └── Breaking changes detection
│
└── Full E2E: Complete customer journey
```

---

## 4. MARQED ALS EIGEN KLANT (Dogfooding)

### 4.1 Waarom Dit Belangrijk Is

- **Directe feedback:** We ervaren zelf wat klanten ervaren
- **FP Tracking:** Inzicht in eigen development effort
- **Showcase:** Demo-able voor prospects
- **Kwaliteitsborging:** Bugs worden direct gevoeld

### 4.2 Implementatie Plan

```
WEEK 170: MarQed Project Setup
├── Tenant: marqed.ai
├── Project: "MarQed Platform Development"
├── Repositories: MarkdownTaskManager repo
└── Users: Eddie (Admin), Team (diverse rollen)

WEEK 171: Eerste Inschattingen
├── 10 openstaande features inschatten
├── FP bundel: "Ongelimiteerd" (intern)
└── Eerste Brown Paper op eigen codebase

WEEK 175: Live Development Tracking
├── Alle development via eigen platform
├── Kanban board actief gebruiken
├── FP verbruik rapportage
└── Agent activiteit monitoren

WEEK 180: Evaluatie & Aanpassingen
├── Feedback verzamelen van team
├── Usability issues identificeren
├── Performance monitoring
└── Security review eigen data
```

### 4.3 Interne FP Tracking

| Work Type | Estimated | Method | Notes |
|-----------|-----------|--------|-------|
| Fase A (Foundation) | ~120 FP | Development FP | Nieuwe code |
| Fase B (Core) | ~180 FP | Development FP | Nieuwe features |
| Fase C (Workflows) | ~150 FP | Enhancement FP | Bestaande integratie |
| Fase D (Polish) | ~80 FP | Enhancement FP | Refinement |
| **Totaal** | **~530 FP** | | |

Bij 10 FP/maand = 53 maanden? **Nee**, want AI agents versnellen dit significant.
Realistische schatting met AI: **~4-6 maanden** (85-90% AI-assisted)

---

## 5. DELTA BROWN PAPER STRATEGIE

### 5.1 Probleemstelling

Wanneer:
- MarQed doet analyse op codebase
- Andere teams werken ook aan de software
- Geen GitHub toegang voor continue sync
- Periodiek nieuwe code uploads nodig

**Vraag:** Moeten we elke keer een volledige Brown Paper doen?

### 5.2 Aanbevolen Aanpak: Delta Brown Paper

**NEE, geen volledige Brown Paper elke keer.** In plaats daarvan:

```
DELTA BROWN PAPER WORKFLOW

┌─────────────────────────────────────────────────────────────────────────────┐
│ EERSTE KEER: Full Brown Paper                                                │
│ ├── Complete analyse (6 stages)                                             │
│ ├── Baseline metrics opslaan                                                │
│ ├── File hashes opslaan                                                     │
│ └── Story/FP baseline vastleggen                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ VOLGENDE KEREN: Delta Analysis                                               │
│                                                                              │
│ STAP 1: File Diff Detection (< 1 minuut)                                    │
│ ├── Hash vergelijking met baseline                                          │
│ ├── Identificeer: NEW, MODIFIED, DELETED files                              │
│ └── Output: change_manifest.json                                            │
│                                                                              │
│ STAP 2: Impact Analysis (5-10 minuten)                                      │
│ ├── Alleen MODIFIED files analyseren                                        │
│ ├── Dependency impact berekenen                                             │
│ ├── Stories identificeren die geraakt worden                                │
│ └── Output: impact_report.json                                              │
│                                                                              │
│ STAP 3: Delta Estimation (5-10 minuten)                                     │
│ ├── Nieuwe stories inschatten (Eliza)                                       │
│ ├── Bestaande stories herzien indien nodig                                  │
│ ├── FP delta berekenen                                                      │
│ └── Output: delta_estimation.json                                           │
│                                                                              │
│ STAP 4: Client Report Generation (2 minuten)                                │
│ ├── "Wijzigingen sinds laatste analyse"                                     │
│ ├── Nieuwe/gewijzigde stories                                               │
│ ├── FP impact                                                               │
│ └── Output: client_delta_report.pdf                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Technische Implementatie

```python
# Nieuw aan te maken service
class DeltaBrownPaperService:
    """
    Delta analyse voor periodieke code updates zonder GitHub access.
    """

    def __init__(self):
        self.baseline_store = BaselineStore()  # Persist tussen runs
        self.hasher = FileHasher()
        self.impact_analyzer = ImpactAnalyzer()
        self.delta_estimator = DeltaEstimator()

    async def analyze_delta(
        self,
        project_id: str,
        new_code_path: Path,
    ) -> DeltaReport:
        """
        Analyseer delta tussen baseline en nieuwe code.

        Returns:
            DeltaReport met:
            - changed_files: List[FileChange]
            - impacted_stories: List[StoryImpact]
            - fp_delta: FPDelta
            - recommendations: List[str]
        """
        # 1. Laad baseline
        baseline = await self.baseline_store.get(project_id)

        # 2. Bereken file changes
        current_hashes = await self.hasher.hash_directory(new_code_path)
        file_changes = self.compare_hashes(baseline.hashes, current_hashes)

        # 3. Impact analysis (alleen gewijzigde files)
        impacts = await self.impact_analyzer.analyze(
            changed_files=file_changes.modified + file_changes.new,
            baseline_stories=baseline.stories,
        )

        # 4. Delta estimation
        fp_delta = await self.delta_estimator.estimate(
            impacts=impacts,
            baseline_estimates=baseline.estimates,
        )

        # 5. Update baseline
        await self.baseline_store.update(project_id, current_hashes)

        return DeltaReport(
            project_id=project_id,
            analysis_date=datetime.now(),
            file_changes=file_changes,
            impacted_stories=impacts,
            fp_delta=fp_delta,
            full_brownpaper_needed=self.should_full_rescan(file_changes),
        )

    def should_full_rescan(self, changes: FileChanges) -> bool:
        """
        Bepaal of volledige Brown Paper nodig is.

        Triggers voor full rescan:
        - >30% files gewijzigd
        - Nieuwe major modules
        - Database schema changes
        - Architecture changes
        """
        change_ratio = (len(changes.modified) + len(changes.new)) / changes.total_files
        return change_ratio > 0.30 or changes.has_structural_changes
```

### 5.4 Wanneer WEL Full Brown Paper?

| Situatie | Delta OK? | Full Brown Paper? | Reden |
|----------|-----------|-------------------|-------|
| < 20% files gewijzigd | ✅ | ❌ | Incrementeel |
| 20-30% files gewijzigd | ⚠️ | Overwegen | Grensgebied |
| > 30% files gewijzigd | ❌ | ✅ | Te veel impact |
| Nieuwe database tabellen | ❌ | ✅ | Schema impact |
| Nieuwe modules/folders | ❌ | ✅ | Architectuur impact |
| Security gevoelige changes | ❌ | ✅ | Volledige scan nodig |
| > 3 maanden sinds laatste | ❌ | ✅ | Context verloren |

### 5.5 Client Communicatie

**Template voor Delta Report naar klant:**

```markdown
# Wijzigingsrapport - [Project Naam]
**Datum:** [datum]
**Periode:** [vorige analyse] - [huidige analyse]

## Samenvatting
- **Gewijzigde bestanden:** [X] van [Y] totaal ([Z]%)
- **Nieuwe stories geïdentificeerd:** [N]
- **Bestaande stories herzien:** [M]
- **FP Impact:** +[X] FP (nieuw), ±[Y] FP (herzien)

## Nieuwe Functionaliteit Gedetecteerd
| Story | Beschrijving | FP | Status |
|-------|--------------|----|----|
| [ID] | [Beschrijving] | [X] | Nieuw |

## Gewijzigde Stories (FP Herziening)
| Story | Was | Wordt | Delta | Reden |
|-------|-----|-------|-------|-------|
| [ID] | [X] FP | [Y] FP | +[Z] | [Reden] |

## Aanbevelingen
1. [Aanbeveling 1]
2. [Aanbeveling 2]

## Volgende Stappen
- [ ] Klant akkoord op nieuwe stories
- [ ] FP herziening goedkeuren
- [ ] Prioritering bepalen
```

### 5.6 Implementatie Fase

De Delta Brown Paper service wordt geïntegreerd in **Fase 26** (AI & Automation):

| Component | Fase | Week | Effort |
|-----------|------|------|--------|
| DeltaBrownPaperService | 26 | 201-203 | 40h |
| BaselineStore | 26 | 201-202 | 16h |
| FileHasher + Diff | 26 | 202 | 8h |
| ImpactAnalyzer | 26 | 202-203 | 24h |
| DeltaEstimator | 26 | 203 | 16h |
| API Routes | 26 | 203 | 8h |
| Client Report Generator | 26 | 203 | 8h |
| **Totaal** | | | **120h** |

---

## 6. GEDETAILLEERDE TIMELINE

### 6.1 Gantt-style Overview

```
                    JANUARY 2026                 FEBRUARY 2026
Week:    158   159   160   161   162   163   164   165   166   167
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE A   ████████████████████████████████████
Multi-T  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Auth     ░░░░░░░░████████████░░░░░░░░░░░░░░░░
Frontend ░░░░░░░░░░░░░░░░░░░░████████████████

                    FEBRUARY/MARCH 2026
Week:    168   169   170   171   172   173   174   175   176   177
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE B   ████████████████████████████████████
Kanban   ████████████░░░░░░░░░░░░░░░░░░░░░░░░
FP Flow  ░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░
Agent    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░
BrownP   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████

FASE C   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████████████
GreenP   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░
Migrat   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░
Quality  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████

                    MARCH/APRIL 2026
Week:    178   179   180   181   182   183   184   185
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE C   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
WFProg   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░

FASE D   ░░░░░░░░████████████████████████████
Comment  ░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░
Notif    ░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░
Launch   ░░░░░░░░░░░░░░░░░░░░░░░░████████████

MARQED   ░░░░░░░░░░████████████████████████████
Dogfood  Start W170 ─────────────────────────────►
```

### 6.2 Milestones & Checkpoints

| Week | Milestone | Go/No-Go Criteria |
|------|-----------|-------------------|
| **163** | Fase A Complete | 3 tenants isolated, login werkt |
| **167** | Kanban Live | Real-time updates, agent zichtbaar |
| **171** | FP Flow Complete | HCI test doorlopen |
| **175** | Brown Paper Complete | Full workflow op HCI |
| **179** | Fase C Complete | Alle workflows operationeel |
| **183** | Notificaties Live | Email + in-app |
| **185** | Launch Ready | Security audit passed |

### 6.3 Resource Toewijzing

**AI Agents per Fase:**

| Fase | Primary Agents | Supporting | Human Review |
|------|---------------|------------|--------------|
| A | Felix (code), Quinn (security) | Miguel (testing) | Architecture decisions |
| B | Felix (frontend), Miguel (backend) | Peter (specs) | UX decisions |
| C | Peter, Betty, Felix | Eliza, Paul | Workflow validation |
| D | Diana (docs), Tessa (testing) | Quinn | Final QA |

**Schatting AI vs Human Effort:**

| Fase | AI Effort | Human Review | Total |
|------|-----------|--------------|-------|
| A | 85% | 15% | 240h (~120h AI-equivalent) |
| B | 90% | 10% | 320h |
| C | 90% | 10% | 320h |
| D | 80% | 20% | 240h |
| **Totaal** | **87%** | **13%** | **1120h** |

---

## 7. RISICO'S EN MITIGATIES

### 7.1 Technische Risico's

| Risico | Impact | Waarschijnlijkheid | Mitigatie |
|--------|--------|-------------------|-----------|
| Multi-tenant data leak | CRITICAL | Low | RLS + audit logging + penetration test |
| WebSocket performance | HIGH | Medium | Load test met 50 concurrent users |
| Agent response time | MEDIUM | Medium | Caching, queue management |
| LLM API rate limits | MEDIUM | Low | Fallback providers, request batching |

### 7.2 Project Risico's

| Risico | Impact | Waarschijnlijkheid | Mitigatie |
|--------|--------|-------------------|-----------|
| Scope creep | HIGH | High | Strikte P1/P2/P3 prioritering |
| Integratie complexiteit | MEDIUM | Medium | Incremental integration, feature flags |
| Test data availability | MEDIUM | Low | 3 echte projecten als test data |
| Team bandwidth | HIGH | Medium | AI-first development, parallel work |

---

## 8. SUCCESS METRICS

### 8.1 Launch Criteria

| Metric | Target | Measure |
|--------|--------|---------|
| **Security** | 0 critical vulnerabilities | Penetration test |
| **Performance** | < 2s page load | Lighthouse score |
| **Uptime** | 99.5% | Monitoring |
| **Tenant Isolation** | 100% | Automated tests |
| **FP Accuracy** | ±20% variance | Historical comparison |

### 8.2 Post-Launch KPIs (3 maanden)

| KPI | Target | Why |
|-----|--------|-----|
| Active Tenants | 3+ | Product-market fit |
| FP Verbruik | 30+ FP/maand totaal | Revenue indicator |
| User Satisfaction | 4+ / 5 | NPS survey |
| Support Tickets | < 5/week/tenant | Quality indicator |
| Agent Utilization | > 70% | Platform value |

---

## Document History

| Versie | Datum | Auteur | Wijzigingen |
|--------|-------|--------|-------------|
| 1.0 | 2026-01-15 | Claude Code | Initial roadmap document |

---

*Gegenereerd: Week 158 (2026-01-15)*
*Volgende review: Week 160 na Fase A start*
