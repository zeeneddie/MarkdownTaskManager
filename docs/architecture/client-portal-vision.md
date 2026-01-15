# MarQed.ai Klantportal - Complete Vision Document

**Versie:** 3.0
**Datum:** 2026-01-15
**Status:** CONCEPT - Compleet met multi-tenant, security, comments en workflow progress

---

## 1. INLEIDING

Dit document beschrijft de complete visie voor het MarQed.ai klantportal. Het portal biedt klanten inzicht in hun projecten, de mogelijkheid om wensen/bugs in te dienen, en transparantie over het werk dat AI agents uitvoeren.

### 1.1 Kernprincipe

> **Elk stuk werk is onderbouwd met een functiepunten (FP) analyse en uitlegbaar aan de klant.**

### 1.2 Unique Selling Point

Klanten zien welke AI agent aan hun werk werkt, met live voortgang. Dit biedt ongekende transparantie in het development proces.

---

## 2. DATASTRUCTUUR

### 2.1 Hiërarchie

```
KLANT (Tenant)
├── Abonnement (FP bundel, SLA level)
├── Users (met rollen)
│
├── PROJECT A
│   ├── Repository 1
│   ├── Repository 2
│   │
│   ├── EPIC 1 (grote business capability)
│   │   ├── FEATURE 1.1 (functionele eenheid)
│   │   │   ├── STORY 1.1.1 (kleinste gebruikerswaarde)
│   │   │   ├── STORY 1.1.2
│   │   │   └── STORY 1.1.3
│   │   └── FEATURE 1.2
│   │       └── ...
│   └── EPIC 2
│       └── ...
│
└── PROJECT B
    └── ...
```

### 2.2 Definities (Marktstandaard)

| Niveau | Definitie | Kenmerken |
|--------|-----------|-----------|
| **Epic** | Grote business capability | Te groot voor 1 sprint, eigen business doel, weken-maanden |
| **Feature** | Functionele eenheid binnen Epic | 1-3 sprints, testbaar als geheel |
| **User Story** | Kleinste eenheid gebruikerswaarde | Past in 1 sprint, INVEST criteria, acceptance criteria |
| **Bug** | Bestaande functie werkt niet zoals gespecificeerd | Correctief werk |

### 2.3 INVEST Criteria (Stories)

- **I**ndependent - Op zichzelf staand
- **N**egotiable - Bespreekbaar
- **V**aluable - Levert waarde
- **E**stimable - In te schatten
- **S**mall - Klein genoeg voor 1 sprint
- **T**estable - Testbaar met acceptance criteria

---

## 3. FUNCTIEPUNTEN MODEL

### 3.1 Work Types (NESMA/IFPUG)

| Type | Nederlands | FP? | Methode | Wanneer |
|------|------------|-----|---------|---------|
| **ANALYSIS** | Analyse | ❌ | Time & Materials | Voortraject (gratis, AI doet dit) |
| **DEVELOPMENT** | Nieuwe bouw | ✅ | Development FP | Green Paper projecten |
| **ENHANCEMENT** | Verbouw | ✅ | Enhancement FP | Wijzigingen, bug fixes |
| **REBUILD** | Herbouw | ✅ | Rebuild FP | Legacy replacement |
| **MAINTENANCE** | Onderhoud | Zie 3.2 | Zie 3.2 | Lopend beheer |

### 3.2 Maintenance Onderverdeling

| Subtype | Beschrijving | FP? |
|---------|--------------|-----|
| **Correctief** | Bug fixen | ✅ Enhancement FP |
| **Adaptief** | Framework/security updates | ✅ Enhancement FP |
| **Perfectief** | Performance, refactoring | ✅ Enhancement FP |
| **Operationeel** | Monitoring, backup, support | ❌ SLA uren |

### 3.3 Abonnementsmodel

```
KLANT ABONNEMENT
├── FP Bundel: 10 FP/maand voor €3.000
├── SLA Level: Goud / Zilver / Brons
├── Overschrijding: Toegestaan (Flex) of Niet (Fixed)
│
├── DEVELOPMENT/ENHANCEMENT/CORRECTIEF/ADAPTIEF/PERFECTIEF
│   └── Verbrandt FP uit bundel
│
└── OPERATIONEEL ONDERHOUD
    └── Apart: SLA uren (niet uit FP bundel)
```

### 3.4 FP Inschatting Flow

```
KLANT SCHIET IN
    ↓
PETER CLASSIFICEERT (Epic/Feature/Story/Bug)
    ↓
SUPERVISOR REVIEWT CLASSIFICATIE
    ↓
ELIZA SCHAT FP IN (met onderbouwing)
    ↓
SUPERVISOR ACCORDEERT INSCHATTING
    ↓
KLANT ZIET RESULTAAT + GEEFT AKKOORD
    ↓
FP WORDT VAN BUNDEL AFGESCHREVEN
```

### 3.5 FP Onderbouwing (voor klant leesbaar)

Elke inschatting bevat:
- FP-componenten (ILF, EIF, EI, EO, EQ)
- Complexiteit per component (laag/gemiddeld/hoog)
- Reden voor complexiteit
- Totaal + berekening
- Impact op bestaande functionaliteit

---

## 4. WORKFLOWS

### 4.1 Workflow Overzicht

| Workflow | Doel | Trigger | Output |
|----------|------|---------|--------|
| **Quickscan** | Go/No-Go beslissing | Sales vraag | Advies + grove inschatting |
| **Green Paper** | Nieuw project specificeren | Nieuw project / NO-GO | Specs + Epics/Features/Stories |
| **Brown Paper** | Bestaande code analyseren | Bestaand project na akkoord | Analyse + Stories + FP |
| **Migration** | Migratieplan maken | Na Brown Paper (optioneel) | Migratieplan + waves |
| **Quality** | Kwaliteit meten | Periodiek of op vraag | Quality rapport |
| **Maintenance** | Onderhoud uitvoeren | Periodiek of op vraag | Fixes + updates |

### 4.2 Quickscan (Sales)

**Doel:** 15-minuten assessment voor Go/No-Go beslissing

**Deployment:**
- Portal mode: Via hub, remote repo of lokaal pad
- Offline mode: Bij klant zonder internet (privacy/security)
  - Desktop app (eigen laptop)
  - Portable/USB (klant PC, zero footprint)

**Output:**
- Dashboard (toonbaar aan klant)
- PDF export
- Techstack detectie
- Advies: GO / CONDITIONAL / NO-GO
- Aanbevolen aanpak: Rehost / Replatform / Refactor / Rebuild / Replace

### 4.3 Green Paper (Nieuw project)

**Triggers:**
- Quickscan met NO-GO (legacy niet te redden)
- Klant vraagt direct iets nieuws
- Uitbreiding niet mogelijk (complexiteit/techstack)

**Flow:**
1. 6 vragen samen met klant doorlopen
2. Peter genereert Constitution
3. Felix genereert Specification (HLD)
4. Felix breakdown naar Epics/Features/Stories
5. Eliza schat FP in
6. Klant ziet en accordeert

### 4.4 Brown Paper (Bestaand project)

**Doel:** Diepgaande analyse van bestaande codebase

**Flow:**
1. Code Understanding (Miguel)
2. Domain Extraction (Peter, Betty)
3. Story Extraction (Peter)
4. Deep Extraction (Felix, Quinn, Marcus)
5. FP Estimation (Eliza)
6. Output Consolidation (Diana)

**Na Brown Paper:**
- Optie A: Migration workflow (als klant migratie wil)
- Optie B: Maintenance workflow (beheer bestaande code)

### 4.5 Workflow → Artifact Mapping

```
INTAKE
├── Klant schiet wens in ──────────────► BACKLOG ITEM
├── Peter classificeert ───────────────► Type (Epic/Feature/Story/Bug)
└── Eliza schat in ────────────────────► FP + Onderbouwing

GREEN PAPER
├── 6 vragen beantwoorden ─────────────► Constitution
├── Felix maakt spec ──────────────────► HLD / Architecture
└── Felix breakdown ───────────────────► Epics → Features → Stories

BROWN PAPER
├── Miguel scant code ─────────────────► Code metrics
├── Peter extraheert domeinen ─────────► Business domains
├── Peter extraheert stories ──────────► User stories
└── Eliza schat in ────────────────────► FP + Effort

COÖRDINATIE
├── Paul plant ────────────────────────► Sprints / Releases
├── Quinn reviewed ────────────────────► Code reviews
└── Diana documenteert ────────────────► Documentation
```

---

## 5. AI AGENTS TEAM

### 5.1 Het Team

```
PROJECT TEAM
├── AI AGENTS (vast per type werk)
│   ├── Peter    - Classificatie, Requirements, Product Owner
│   ├── Betty    - Business Analyse
│   ├── Felix    - Architectuur, Specs, Code
│   ├── Eliza    - FP Inschatting
│   ├── Quinn    - Quality Review, Code Review
│   ├── Miguel   - Code Analyse, Metrics
│   ├── Marcus   - Maintenance, Refactoring
│   ├── Tessa    - Testing
│   ├── Paul     - Planning
│   ├── Diana    - Documentatie
│   └── Vicky    - UX Design
│
└── SUPERVISOR (Mens)
    └── Accordeert, bewaakt, corrigeert
```

### 5.2 Transparantie naar klant

Klant ziet in portal:
- Welke agent aan hun item werkt
- Wat de agent doet ("Classificeren", "FP inschatten", "Spec schrijven")
- Voortgang (progress bar)
- Wanneer supervisor heeft geaccordeerd

---

## 6. PLANNING MODEL

### 6.1 Hybride Aanpak

**Op projectniveau (vast):**
- Fasen (Analyse → Ontwerp → Bouw → Test → Oplevering)
- Milestones
- Afhankelijkheden tussen projecten
- Resources

**Op sprint niveau (agile):**
- Sprints (1-4 weken)
- Kanban board
- Backlog refinement
- Burndown

### 6.2 Sprint Planning met FP Budget

```
SPRINT PLANNING CHECK
├── Item X: 5 FP
├── Beschikbaar deze maand: 3 FP
│
├── Klant "Flex" abonnement:
│   └── ✅ Kan in sprint, 2 FP meerprijs
│
└── Klant "Fixed" abonnement:
    └── ⏸️ Wacht tot volgende maand (nieuwe bundel)
```

---

## 7. 9-LANE KANBAN SYSTEEM

### 7.1 Lane Structuur

**Standaard Lanes (7):**

| Lane | Agent(s) | Quality Gate | Bij falen |
|------|----------|--------------|-----------|
| BACKLOG | - | - | - |
| ANALYSIS | Quinn, Eliza | estimation_complete | → HUMAN_NEEDED |
| DESIGN | Felix | design_approved | → HUMAN_NEEDED |
| BUILD | Felix | code_complete | → HUMAN_NEEDED |
| TEST | Tessa | tests_pass | → BUILD (retry, max 3x) |
| IN_REVIEW | Quinn | review_approved | → BUILD |
| DONE | - | - | - |

**Special Lanes (2):**

| Lane | Beschrijving | Zichtbaar voor klant |
|------|--------------|---------------------|
| HUMAN_NEEDED | Menselijke beslissing nodig | Zie sectie 7.3 |
| BLOCKED | Externe afhankelijkheid | Zie sectie 7.3 |

### 7.2 Automatische Lane Progressie

```
Agent werk klaar
    ↓
Quality Gate check
    ↓
┌─────────┬─────────┬───────────┐
│ PASS    │ FAIL    │ ESCALATE  │
│ → Next  │ → Retry │ → Human   │
│   Lane  │   (max  │   Needed  │
│         │    3x)  │           │
└─────────┴─────────┴───────────┘
    ↓
WebSocket broadcast → Dashboard update live
```

### 7.3 Klant View: "Aandacht Nodig" Sectie

Items in HUMAN_NEEDED of BLOCKED blijven zichtbaar voor klant:

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ AANDACHT NODIG (2)                                           │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────┐  ┌─────────────────────────┐       │
│ │ 🔴 DigiD Koppeling      │  │ 🟡 SMS Gateway          │       │
│ │ 22 FP                   │  │ 6 FP                    │       │
│ │ Wacht op uw input       │  │ Externe afhankelijkheid │       │
│ │ "Keuze: variant A of B" │  │ "Wacht op SMS provider" │       │
│ │ [REAGEREN]              │  │ [MEER INFO]             │       │
│ └─────────────────────────┘  └─────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

**Mapping intern → klant:**

| Interne status | Klant ziet | Waar |
|----------------|------------|------|
| HUMAN_NEEDED (jullie actie) | Badge "In behandeling" | Normale lane |
| HUMAN_NEEDED (klant actie) | "Wacht op uw input" | Aandacht Nodig |
| BLOCKED (extern) | "Externe afhankelijkheid" | Aandacht Nodig |
| BLOCKED (klant actie) | "Wacht op uw actie" | Aandacht Nodig |

### 7.4 Live Dashboard (WebSocket)

Real-time updates zonder refresh:
- Kaartjes verschuiven automatisch
- Agent activiteit live zichtbaar
- Progress bars updaten
- Notificaties bij statuswijziging

---

## 8. KLANT PORTAL FUNCTIES

### 8.1 Klant Rollen Overzicht

| Rol | Ziet | Kan doen |
|-----|------|----------|
| **Viewer** | Voortgang, status | Alleen kijken |
| **Indiener** | + Backlog | Wensen/bugs inschieten |
| **Accordeerder** | + Inschattingen | GO geven op FP verbranding |
| **Manager** | + Rapportages, KPI's | Overzichten, exports, drill-down |
| **Admin** | + Alles | Users beheren, facturatie, configuratie |

**Flexibiliteit:** Één user kan meerdere rollen hebben (bijv. Indiener + Accordeerder bij kleine klant).

### 8.2 Unified Entry Point (Na Login)

Alle users komen op dezelfde entry point - projectoverzicht met rol-afhankelijke extra's:

```
LOGIN
  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 🏠 MIJN PROJECTEN                                               │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌─────────────────────┐               │
│ │ 📁 Patiëntenportaal │  │ 📁 HR Systeem       │               │
│ │ Rollen: Indiener,   │  │ Rollen: Viewer      │               │
│ │         Accordeerder│  │                     │               │
│ │ [OPENEN]            │  │ [OPENEN]            │               │
│ └─────────────────────┘  └─────────────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│ 🔘 EXTRA (rol-afhankelijk)                                      │
│ ├── [📊 DASHBOARDS]        ← Manager + Admin                   │
│ ├── [👥 USER MANAGEMENT]   ← Admin only                        │
│ └── [💰 FACTURATIE]        ← Admin only                        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Granulaire Rechten (Epic/Feature Niveau)

Rechten kunnen per Epic en Feature worden ingesteld met overerving:

**Overerving Model:**
```
RECHTEN STRUCTUUR
│
├── PROJECT niveau (basis)
│   └── User X: Indiener op Project
│       → Default: GEEN rechten op Epics (explicit toekennen)
│
├── EPIC niveau
│   └── User X: Indiener op Epic "WBSO"
│       → Automatisch: rechten op ALLE Features + Stories eronder
│
├── FEATURE niveau (override)
│   └── User X: GEEN rechten op Feature "Login"
│       → Override: blokkeert deze branch, rest Epic blijft
│
└── OVERERVING REGELS
    ├── Epic recht → alle Features + Stories eronder
    ├── Feature recht → alle Stories eronder
    └── Expliciete BLOCK → overschrijft overerving
```

**Admin UI voor rechten instellen:**
```
👥 RECHTEN: Jan de Vries @ Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ QUICK SETTINGS                                                  │
│ ○ Alles                    (alle Epics/Features/Stories)        │
│ ○ Niets                    (alleen lezen)                       │
│ ● Custom                   (per Epic/Feature instellen)         │
├─────────────────────────────────────────────────────────────────┤
│ CUSTOM RECHTEN                                                  │
│                                                                 │
│ 📋 Epic: Gebruikersbeheer                                       │
│    [Indiener ▼] ☑️ Inclusief alle Features                      │
│    │                                                            │
│    ├── Feature: Login                                           │
│    │   [🚫 Geen ▼]  ← EXCEPTION (override)                      │
│    │                                                            │
│    └── Feature: Wachtwoord reset                                │
│        [Overgeërfd ▼] (= Indiener)                              │
│                                                                 │
│ 📋 Epic: WBSO Registratie                                       │
│    [Indiener ▼] ☑️ Inclusief alle Features                      │
│                                                                 │
│ 📋 Epic: Facturatie                                             │
│    [🚫 Geen ▼]                                                  │
│    │                                                            │
│    └── Feature: Factuur export                                  │
│        [Indiener ▼]  ← EXCEPTION (toch toestaan)                │
├─────────────────────────────────────────────────────────────────┤
│ [OPSLAAN]  [ANNULEREN]                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Rechten Opties per niveau:**

| Optie | Betekenis |
|-------|-----------|
| **Geen** | Alleen lezen |
| **Viewer** | Lezen + comments |
| **Indiener** | + Nieuw toevoegen + wijzigen + verwijderen |
| **Accordeerder** | + FP goedkeuren |
| **Overgeërfd** | Volgt parent (Epic/Feature) |

---

### 8.4 VIEWER - Project View (Readonly)

**Wat Viewer ziet bij openen project:**

```
📁 PROJECT: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ 📊 VOORTGANG                                                    │
│ ████████████░░░░ 72% compleet                                   │
│ Sprint 14 │ 8 items in progress │ 3 items done deze week       │
├─────────────────────────────────────────────────────────────────┤
│ 📋 PROJECTSTRUCTUUR                    [Kanban ▼] [Lijst ▼]    │
│                                                                 │
│ 📋 EPIC: Gebruikersbeheer (42 FP)                               │
│    ├── ✅ Feature: Login (8 FP)                    Done        │
│    ├── 🔄 Feature: Wachtwoord reset (6 FP)         In progress │
│    │   ├── ✅ Story: Reset via email               Done        │
│    │   ├── 🔄 Story: Reset via SMS                 BUILD       │
│    │   │      └── 🤖 Felix aan het werk (78%)                  │
│    │   └── ⏳ Story: Reset via WhatsApp            Backlog     │
│    └── ⏳ Feature: 2FA (12 FP)                     Gepland S16 │
│                                                                 │
│ 📋 EPIC: WBSO Registratie (28 FP)                               │
│    ├── ✅ Feature: Urenregistratie (15 FP)         Done        │
│    └── 🔄 Feature: Rapportage (13 FP)              TEST        │
│          └── 🤖 Tessa aan het werk (45%)                       │
│                                                                 │
│ 📋 EPIC: Facturatie (35 FP)                                     │
│    └── ⏳ Nog niet gestart                         Backlog     │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AGENTS ACTIVE                                                │
│ ├── Felix  → SMS Reset implementatie    ████████░░ 78%         │
│ └── Tessa  → Rapportage tests           █████░░░░░ 45%         │
├─────────────────────────────────────────────────────────────────┤
│ 📅 RECENTE ACTIVITEIT                                           │
│ ├── Vandaag 14:32 - Story "Reset via email" → Done             │
│ ├── Vandaag 11:15 - Felix started "Reset via SMS"              │
│ └── Gisteren - Feature "Login" opgeleverd                      │
└─────────────────────────────────────────────────────────────────┘
```

**Viewer Kanban (readonly):**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 KANBAN                                        [Filters ▼]   │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────────┤
│ BACKLOG │ ANALYSIS│ DESIGN  │ BUILD   │ TEST    │ DONE        │
│ (3)     │ (1)     │ (0)     │ (2)     │ (1)     │ (12)        │
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────────┤
│┌───────┐│┌───────┐│         │┌───────┐│┌───────┐│┌───────┐    │
││2FA    │││Export ││         ││SMS    │││Rapport││✅ Login│    │
││12 FP  │││⏳Eliza││         ││🤖Felix││││🤖Tessa││8 FP   │    │
│└───────┘│└───────┘│         ││6 FP   ││└───────┘│└───────┘    │
│┌───────┐│         │         │└───────┘│         │             │
││WhatsAp││         │         │┌───────┐│         │             │
││4 FP   ││         │         ││Bug #42││         │             │
│└───────┘│         │         ││3 FP   ││         │             │
│         │         │         │└───────┘│         │             │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────────┘
│ 👁️ READONLY - Alleen kijken                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Viewer = Stakeholder view** - ziet voortgang, kan niets aanpassen. Ideaal voor:
- Management dat wil meekijken
- Externe stakeholders
- Collega's uit andere afdelingen

---

### 8.5 INDIENER - Project View

**Wat Indiener ziet bij openen project:**

```
📁 PROJECT: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Filter: [Alles ▼] [Mijn items ▼]          [+ NIEUW INDIENEN] │
├─────────────────────────────────────────────────────────────────┤
│ 📋 EPIC: Gebruikersbeheer                    🔒 Geen rechten    │
│    └── (ingeklapt, alleen lezen)                                │
│                                                                 │
│ 📋 EPIC: WBSO Registratie                    ✅ Indiener        │
│    ├── Feature: Urenregistratie              ✅ (overgeërfd)    │
│    │   ├── Story: Uren invoeren              ✅                 │
│    │   └── Story: Uren goedkeuren            ✅                 │
│    │   └── [+ STORY TOEVOEGEN]                                  │
│    ├── Feature: Rapportage                   ✅ (overgeërfd)    │
│    └── [+ FEATURE TOEVOEGEN]                                    │
│                                                                 │
│ 📋 EPIC: Facturatie                          ⚠️ Deels           │
│    ├── Feature: Login                        🔒 Geen rechten    │
│    └── Feature: Factuur export               ✅ Indiener        │
│        └── [+ STORY TOEVOEGEN]                                  │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AGENTS ACTIVE                                                │
│ ├── Felix  → SMS Reset implementatie    ████████░░ 78%         │
│ └── Tessa  → Rapportage tests           █████░░░░░ 45%         │
├─────────────────────────────────────────────────────────────────┤
│ 📅 RECENTE ACTIVITEIT                                           │
│ ├── Vandaag 14:32 - Story "Reset via email" → Done             │
│ └── Vandaag 11:15 - Felix started "Reset via SMS"              │
└─────────────────────────────────────────────────────────────────┘
```

**Indiener rechten indicatie:**
- ✅ = Kan indienen/wijzigen/verwijderen
- 🔒 = Alleen lezen (geen rechten)
- ⚠️ = Deels (sommige children wel, andere niet)

---

### 8.6 ACCORDEERDER - Project View

**Wat Accordeerder ziet bij openen project:**

```
📁 PROJECT: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ ⚠️ WACHT OP UW AKKOORD (3)                                      │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🟠 DigiD Koppeling                              22 FP       │ │
│ │ Epic: Gebruikersbeheer → Feature: Login                     │ │
│ │ Ingediend door: Jan de Vries │ 2 dagen geleden              │ │
│ │                                                             │ │
│ │ 📄 Onderbouwing:                                            │ │
│ │ • 2x EIF (DigiD, BSN registry) = 10 FP                      │ │
│ │ • 1x EI (Login flow) = 4 FP                                 │ │
│ │ • 2x EO (Status, Foutmelding) = 8 FP                        │ │
│ │                                                             │ │
│ │ [✅ AKKOORD 22 FP]  [❌ AFWIJZEN]  [💬 VRAAG STELLEN]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🟠 SMS Gateway koppeling                        6 FP        │ │
│ │ Epic: WBSO → Feature: Notificaties                          │ │
│ │ [BEKIJKEN]                                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🟠 Bug: Export faalt bij >1000 regels           3 FP        │ │
│ │ Epic: Facturatie → Feature: Export                          │ │
│ │ [BEKIJKEN]                                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 📊 FP BUDGET DEZE MAAND                                         │
│ ████████░░░░░░░░ 45/100 FP verbruikt                           │
│ Na akkoord: 76/100 FP (+31 FP pending)                          │
├─────────────────────────────────────────────────────────────────┤
│ 📋 PROJECTSTRUCTUUR                    [Kanban ▼] [Lijst ▼]    │
│                                                                 │
│ 📋 EPIC: Gebruikersbeheer              ✅ Accordeerder          │
│    ├── Feature: Login         🟠 1 wacht op akkoord            │
│    └── Feature: Wachtwoord    ✅ 6 FP geaccordeerd             │
│                                                                 │
│ 📋 EPIC: WBSO                          ✅ Accordeerder          │
│    └── Feature: Notificaties  🟠 1 wacht op akkoord            │
│                                                                 │
│ 📋 EPIC: Facturatie                    🔒 Geen rechten          │
│    └── (alleen lezen)                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Accordeerder Detail View (bij klik op item):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📄 ACCORDERING: DigiD Koppeling                                 │
├─────────────────────────────────────────────────────────────────┤
│ TYPE: Feature (nieuw)                                           │
│ CLASSIFICATIE: Development FP                                   │
│ GECLASSIFICEERD DOOR: Peter (AI) ✓ Supervisor akkoord          │
├─────────────────────────────────────────────────────────────────┤
│ 📊 FP ONDERBOUWING                                              │
│                                                                 │
│ Data Functies:                                                  │
│ ├── EIF: DigiD Metadata         (7 DET, 2 RET) = 5 FP          │
│ └── EIF: BSN Registry           (5 DET, 1 RET) = 5 FP          │
│                                                                 │
│ Transactie Functies:                                            │
│ ├── EI: DigiD Login Request     (6 DET, 2 FTR) = 4 FP          │
│ ├── EO: Login Status Response   (8 DET, 2 FTR) = 5 FP          │
│ └── EO: Foutmelding             (4 DET, 1 FTR) = 3 FP          │
│                                                                 │
│ TOTAAL: 22 FP                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 📅 IMPACT OP BUDGET                                             │
│ Huidig verbruik:     45 FP                                      │
│ Dit item:           +22 FP                                      │
│ Na akkoord:          67 FP (binnen bundel ✅)                   │
├─────────────────────────────────────────────────────────────────┤
│ 📅 MOGELIJKE OPLEVERING                                         │
│ Bij akkoord vandaag: Sprint 16 (week 8)                         │
├─────────────────────────────────────────────────────────────────┤
│ 💬 OPMERKINGEN                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Jan: "Graag met terugval naar wachtwoord als DigiD faalt"   │ │
│ │ Peter (AI): "Toegevoegd als acceptatiecriterium"            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [+ Opmerking toevoegen]                                         │
├─────────────────────────────────────────────────────────────────┤
│ [✅ AKKOORD 22 FP]  [❌ AFWIJZEN]  [↩️ TERUG]                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8.7 MANAGER - Project View

**Wat Manager ziet bij openen project:**

```
📁 PROJECT: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ 📊 KPI DASHBOARD                                 [Exporteer ▼] │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│ │ FP VERBRUIK   │ │ VOORTGANG     │ │ DOORLOOPTIJD  │          │
│ │ 67/100        │ │ 72%           │ │ Ø 4.2 dagen   │          │
│ │ ████████░░    │ │ ████████░░    │ │ ▼ 12% vs vorig│          │
│ │ 33 FP resterend│ │ 28 FP pending │ │ SLA: ✅ OK    │          │
│ └───────────────┘ └───────────────┘ └───────────────┘          │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│ │ ITEMS ACTIVE  │ │ WACHT OP      │ │ OPGELEVERD    │          │
│ │ 8             │ │ AKKOORD: 3    │ │ DEZE MAAND: 12│          │
│ │ 🤖 4 bij agent│ │ KLANT: 2      │ │ ▲ 20% vs vorig│          │
│ │ 👤 2 bij mens │ │ EXTERN: 1     │ │ 45 FP waarde  │          │
│ └───────────────┘ └───────────────┘ └───────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│ 📈 TRENDS                                        [Periode ▼]   │
│                                                                 │
│ FP Verbruik (6 maanden)          Velocity (stories/sprint)     │
│ 20│    ╭─╮                       8│       ╭───╮                │
│ 15│ ╭──╯ ╰──╮                    6│   ╭───╯   ╰──              │
│ 10│─╯       ╰──                  4│───╯                        │
│  5│                              2│                            │
│   └─────────────────              └─────────────────           │
│    J  F  M  A  M  J               S10 S11 S12 S13 S14          │
├─────────────────────────────────────────────────────────────────┤
│ 📋 EPICS OVERZICHT (klik voor drill-down)       [▼ Details]    │
│                                                                 │
│ Epic                    FP     Voortgang    Status    Forecast │
│ ─────────────────────────────────────────────────────────────  │
│ Gebruikersbeheer        42     ████████░░   78%      Sprint 16 │
│ WBSO Registratie        28     ██████████   100%     ✅ Done   │
│ Facturatie              35     ░░░░░░░░░░   0%       Sprint 18 │
│ ─────────────────────────────────────────────────────────────  │
│ TOTAAL                  105    ████████░░   72%                │
├─────────────────────────────────────────────────────────────────┤
│ ⚠️ AANDACHTSPUNTEN                                              │
│ ├── 🟠 3 items wachten >2 dagen op klant akkoord               │
│ ├── 🟡 FP bundel op 67% - nog 5 weken tot vernieuwing          │
│ └── 🟢 SLA: alle items binnen norm                             │
├─────────────────────────────────────────────────────────────────┤
│ [📋 KANBAN]  [📄 RAPPORT GENEREREN]  [📊 UITGEBREIDE ANALYSE]  │
└─────────────────────────────────────────────────────────────────┘
```

**Manager Epic Drill-down:**

```
📋 EPIC: Gebruikersbeheer                          [↩️ Terug]
├─────────────────────────────────────────────────────────────────┤
│ 📊 EPIC KPIs                                                    │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│ │ FP TOTAAL     │ │ FP VERBRUIKT  │ │ FP RESTEREND  │          │
│ │ 42            │ │ 33            │ │ 9             │          │
│ └───────────────┘ └───────────────┘ └───────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│ 📋 FEATURES BREAKDOWN                                           │
│                                                                 │
│ Feature              FP    Status         Agent      Doorloop  │
│ ────────────────────────────────────────────────────────────── │
│ Login                8     ✅ Done        -          3.2 dagen │
│ Wachtwoord reset     6     🔄 BUILD       Felix      4.1 dagen │
│ 2FA                  12    ⏳ Backlog     -          -         │
│ DigiD Koppeling      22    🟠 Wacht akk.  -          -         │
├─────────────────────────────────────────────────────────────────┤
│ 👥 BETROKKENEN                                                  │
│ ├── Indieners: Jan de Vries, Petra Smit                        │
│ ├── Accordeerder: Klaas Bakker                                 │
│ └── Agents: Felix (78%), Tessa (queue)                         │
├─────────────────────────────────────────────────────────────────┤
│ 📈 BURNDOWN EPIC                                                │
│ 42│▓▓▓▓                                                        │
│ 30│    ▓▓▓▓                                                    │
│ 20│        ▓▓▓▓──── actueel                                    │
│ 10│            ╲___ gepland                                    │
│  0│                    ╲                                       │
│   └─────────────────────────                                   │
│    S12  S13  S14  S15  S16                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Manager Rapport Genereren:**

```
📄 RAPPORT GENEREREN
├─────────────────────────────────────────────────────────────────┤
│ TYPE RAPPORT                                                    │
│ ○ Voortgangsrapport (weekly/monthly)                           │
│ ○ FP Verbruik overzicht                                        │
│ ○ Epic status rapport                                          │
│ ● Custom rapport                                                │
├─────────────────────────────────────────────────────────────────┤
│ INHOUD SELECTEREN                                               │
│ ☑️ KPI samenvatting                                             │
│ ☑️ FP verbruik breakdown                                        │
│ ☑️ Epic/Feature voortgang                                       │
│ ☐ Gedetailleerde story status                                  │
│ ☑️ Doorlooptijd analyse                                         │
│ ☐ Agent activiteit log                                         │
├─────────────────────────────────────────────────────────────────┤
│ PERIODE: [Deze maand ▼]                                         │
├─────────────────────────────────────────────────────────────────┤
│ [📥 DOWNLOAD PDF]  [📧 EMAIL NAAR...]  [ANNULEREN]             │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8.8 ADMIN - Project View

**Wat Admin ziet bij openen project:**

```
📁 PROJECT: Patiëntenportaal                    [⚙️ INSTELLINGEN]
├─────────────────────────────────────────────────────────────────┤
│ 🔧 ADMIN QUICK ACTIONS                                          │
│ [👥 Users & Rechten]  [💰 Facturatie]  [⚙️ Config]  [📋 Audit] │
├─────────────────────────────────────────────────────────────────┤
│ 📊 KPI DASHBOARD                                 [Exporteer ▼] │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│ │ FP VERBRUIK   │ │ VOORTGANG     │ │ DOORLOOPTIJD  │          │
│ │ 67/100        │ │ 72%           │ │ Ø 4.2 dagen   │          │
│ │ ████████░░    │ │ ████████░░    │ │ ▼ 12% vs vorig│          │
│ │ €2.010 waarde │ │ 28 FP pending │ │ SLA: ✅ OK    │          │
│ └───────────────┘ └───────────────┘ └───────────────┘          │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│ │ 💰 BUDGET     │ │ 📅 CONTRACT   │ │ ⚠️ ALERTS     │          │
│ │ €6.700/€10K   │ │ Verloopt over │ │ 2 actief      │          │
│ │ maand 67%     │ │ 87 dagen      │ │ [Bekijk]      │          │
│ └───────────────┘ └───────────────┘ └───────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│ 👥 PROJECT USERS (5)                             [+ Toevoegen] │
│                                                                 │
│ User              Rollen                    Laatst actief       │
│ ────────────────────────────────────────────────────────────── │
│ Jan de Vries      Indiener, Accordeerder    Vandaag 14:32      │
│ Petra Smit        Manager                   Vandaag 09:15      │
│ Klaas Bakker      Accordeerder              Gisteren           │
│ Lisa Jansen       Viewer                    3 dagen geleden    │
│ Tom de Groot      Indiener                  1 week geleden ⚠️  │
│                                              [Alle users →]     │
├─────────────────────────────────────────────────────────────────┤
│ 📋 EPICS OVERZICHT                              [▼ Details]    │
│ (zelfde als Manager view)                                       │
├─────────────────────────────────────────────────────────────────┤
│ 🔧 TECHNISCH                                                    │
│ ├── Repositories: 2 gekoppeld                                   │
│ ├── Webhooks: 3 actief                                         │
│ ├── API calls deze maand: 1.247                                │
│ └── Storage: 2.3 GB / 10 GB                                    │
├─────────────────────────────────────────────────────────────────┤
│ [📋 KANBAN]  [📄 RAPPORT]  [📊 ANALYSE]  [🗂️ AUDIT LOG]        │
└─────────────────────────────────────────────────────────────────┘
```

**Admin - User Management:**

```
👥 USER MANAGEMENT                                 [+ NIEUWE USER]
├─────────────────────────────────────────────────────────────────┤
│ 👤 Jan de Vries                                                 │
│ ├── Patiëntenportaal: Indiener, Accordeerder  [✏️ WIJZIG]      │
│ ├── HR Systeem: Viewer                        [✏️ WIJZIG]      │
│ └── [+ PROJECT TOEVOEGEN]                                       │
├─────────────────────────────────────────────────────────────────┤
│ 👤 Petra Smit                                                   │
│ ├── Patiëntenportaal: Manager                 [✏️ WIJZIG]      │
│ └── [+ PROJECT TOEVOEGEN]                                       │
├─────────────────────────────────────────────────────────────────┤
│ 👤 Klaas Bakker                               [🗑️ VERWIJDER]   │
│ └── (geen projecten)                                            │
└─────────────────────────────────────────────────────────────────┘
```

**Admin - Facturatie:**

```
💰 FACTURATIE: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ CONTRACT                                                        │
│ ├── Type: Goud SLA                                             │
│ ├── FP Bundel: 100 FP/maand @ €30/FP                          │
│ ├── Maandbedrag: €3.000                                        │
│ ├── Overschrijding: Flex (€35/FP)                              │
│ ├── Startdatum: 01-01-2025                                     │
│ └── Einddatum: 31-12-2025 (nog 87 dagen)                       │
├─────────────────────────────────────────────────────────────────┤
│ VERBRUIK DEZE MAAND                                             │
│ ├── Verbruikt: 67 FP (€2.010)                                  │
│ ├── Pending akkoord: 31 FP (€930)                              │
│ ├── Resterend: 33 FP (€990)                                    │
│ └── Prognose: 98 FP (binnen bundel ✅)                         │
├─────────────────────────────────────────────────────────────────┤
│ FACTUUR HISTORIE                                                │
│                                                                 │
│ Periode        FP      Bedrag     Status      Factuur          │
│ ────────────────────────────────────────────────────────────── │
│ Dec 2024       89      €2.670     ✅ Betaald  [📄 PDF]         │
│ Nov 2024       102     €3.070     ✅ Betaald  [📄 PDF]         │
│ Okt 2024       95      €2.850     ✅ Betaald  [📄 PDF]         │
├─────────────────────────────────────────────────────────────────┤
│ [📄 FACTUUR PREVIEW DEZE MAAND]  [📊 VERBRUIK EXPORT]          │
└─────────────────────────────────────────────────────────────────┘
```

**Admin - Audit Log:**

```
🗂️ AUDIT LOG: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ FILTER: [Alle acties ▼] [Alle users ▼] [Deze maand ▼] [Zoek]  │
├─────────────────────────────────────────────────────────────────┤
│ Timestamp          User/Agent    Actie                         │
│ ────────────────────────────────────────────────────────────── │
│ 15-01 14:32:15    Jan de Vries  Story "Email reset" → Done    │
│ 15-01 14:30:02    🤖 Felix      Code commit: feat/sms-reset   │
│ 15-01 14:28:45    🤖 Quinn      Review approved: SMS reset    │
│ 15-01 11:15:33    🤖 Felix      Started: SMS Reset impl.      │
│ 15-01 10:02:18    Klaas Bakker  ✅ Akkoord: DigiD (22 FP)     │
│ 15-01 09:45:00    🤖 Eliza      FP inschatting: DigiD = 22 FP │
│ 14-01 16:20:11    Admin         User toegevoegd: Tom de Groot │
│ 14-01 15:55:03    Petra Smit    Rapport gedownload            │
│ ...                                                            │
├─────────────────────────────────────────────────────────────────┤
│ [📥 EXPORT AUDIT LOG]                         Pagina 1 van 24  │
└─────────────────────────────────────────────────────────────────┘
```

**Admin - Project Instellingen:**

```
⚙️ PROJECT INSTELLINGEN: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ ALGEMEEN                                                        │
│ Projectnaam:     [Patiëntenportaal____________]                │
│ Klant:           Ziekenhuis Noord (readonly)                   │
│ Status:          [Actief ▼]                                    │
│ SLA Level:       [Goud ▼]                                      │
├─────────────────────────────────────────────────────────────────┤
│ REPOSITORIES                                                    │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🔗 github.com/client/patient-portal     [🗑️] [⚙️]          ││
│ │ 🔗 github.com/client/patient-api        [🗑️] [⚙️]          ││
│ └─────────────────────────────────────────────────────────────┘│
│ [+ Repository toevoegen]                                        │
├─────────────────────────────────────────────────────────────────┤
│ NOTIFICATIES (project defaults)                                 │
│ ☑️ Email bij nieuwe inschattingen                               │
│ ☑️ Slack bij blokkades                                          │
│ ☐ Dagelijkse samenvatting                                      │
│ [Per user aanpassen →]                                          │
├─────────────────────────────────────────────────────────────────┤
│ DANGER ZONE                                                     │
│ [🗄️ Archiveer project]  [🗑️ Verwijder project]                │
├─────────────────────────────────────────────────────────────────┤
│ [OPSLAAN]  [ANNULEREN]                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8.9 Complete Rollen Vergelijking

| Element | Viewer | Indiener | Accordeerder | Manager | Admin |
|---------|--------|----------|--------------|---------|-------|
| **BASIS** |
| Projectstructuur | ✅ | ✅ | ✅ | ✅ | ✅ |
| Kanban board | ✅ RO | ✅ | ✅ | ✅ | ✅ |
| Agent activiteit | ✅ | ✅ | ✅ | ✅ | ✅ |
| Recente activiteit | ✅ | ✅ | ✅ | ✅ | ✅ |
| **INDIENEN** |
| [+ NIEUW INDIENEN] | ❌ | ✅ | Indien rol | Indien rol | ✅ |
| [+ STORY/FEATURE] | ❌ | ✅ | Indien rol | Indien rol | ✅ |
| Wijzigen/Verwijderen | ❌ | ✅ | Indien rol | Indien rol | ✅ |
| **ACCORDEREN** |
| "Wacht op akkoord" sectie | ❌ | ❌ | ✅ | Indien rol | ✅ |
| FP Budget status | ❌ | ❌ | ✅ | ✅ | ✅ |
| [AKKOORD] buttons | ❌ | ❌ | ✅ | Indien rol | ✅ |
| FP onderbouwing detail | Basis | Basis | Volledig | Volledig | Volledig |
| **MANAGEMENT** |
| KPI Dashboard | ❌ | ❌ | ❌ | ✅ | ✅ |
| Trends/Grafieken | ❌ | ❌ | ❌ | ✅ | ✅ |
| Epic drill-down | ❌ | ❌ | ❌ | ✅ | ✅ |
| Rapport genereren | ❌ | ❌ | ❌ | ✅ | ✅ |
| Export functies | ❌ | ❌ | ❌ | ✅ | ✅ |
| **ADMIN** |
| User Management | ❌ | ❌ | ❌ | ❌ | ✅ |
| Rechten beheer | ❌ | ❌ | ❌ | ❌ | ✅ |
| Facturatie/Contract | ❌ | ❌ | ❌ | ❌ | ✅ |
| € bedragen zien | ❌ | ❌ | ❌ | ❌ | ✅ |
| Project instellingen | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit log | ❌ | ❌ | ❌ | ❌ | ✅ |
| Technische info | ❌ | ❌ | ❌ | ❌ | ✅ |

---

### 8.10 Workflow Progress View (Klant)

Klanten kunnen de voortgang van lopende analyses en workflows volgen:

**Entry Point - Project Dashboard:**

```
📁 PROJECT: Patiëntenportaal
├─────────────────────────────────────────────────────────────────┤
│ 🔄 LOPENDE ANALYSES (2)                          [Alle bekijken]│
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📋 Brown Paper Analyse                                       │ │
│ │ Gestart: 14 jan 2026, 09:00                                 │ │
│ │ Fase 4/6: Deep Extraction                                   │ │
│ │ ████████████████░░░░░░░░ 67%                                │ │
│ │ 🤖 Felix en Quinn aan het werk                              │ │
│ │ Geschatte resterende tijd: ~45 minuten                      │ │
│ │ [DETAILS BEKIJKEN]                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📊 Quality Gate Analyse                                      │ │
│ │ Gestart: 14 jan 2026, 14:30                                 │ │
│ │ Fase 2/5: Metrics Analysis                                  │ │
│ │ █████████░░░░░░░░░░░░░░░ 35%                                │ │
│ │ 🤖 Miguel aan het werk                                      │ │
│ │ [DETAILS BEKIJKEN]                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Workflow Detail View:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 BROWN PAPER ANALYSE                             [↩️ Terug]   │
│ Project: Patiëntenportaal                                       │
├─────────────────────────────────────────────────────────────────┤
│ 📊 VOORTGANG                                                    │
│ ████████████████░░░░░░░░ 67%                                   │
│                                                                 │
│ Gestart: 14 jan 2026, 09:00                                    │
│ Geschatte voltooiing: 14 jan 2026, 15:30                       │
├─────────────────────────────────────────────────────────────────┤
│ 📋 FASES                                                        │
│                                                                 │
│ ✅ Fase 1: Code Understanding                    [Voltooid]    │
│    └── 🤖 Miguel │ Duur: 12 min │ 09:00 - 09:12               │
│                                                                 │
│ ✅ Fase 2: Domain Extraction                     [Voltooid]    │
│    └── 🤖 Peter, Betty │ Duur: 25 min │ 09:12 - 09:37         │
│        └── 📄 Output: 8 business domeinen geïdentificeerd      │
│                                                                 │
│ ✅ Fase 3: Story Extraction                      [Voltooid]    │
│    └── 🤖 Peter │ Duur: 35 min │ 09:37 - 10:12                │
│        └── 📄 Output: 42 user stories gegenereerd              │
│                                                                 │
│ 🔄 Fase 4: Deep Extraction                       [Bezig]       │
│    └── 🤖 Felix, Quinn, Marcus │ Gestart: 10:12               │
│        ├── Architecture analysis        ████████████░░ 85%    │
│        ├── Security scanning            ██████████░░░░ 70%    │
│        └── Dependency mapping           ████████░░░░░░ 60%    │
│                                                                 │
│ ⏳ Fase 5: FP Estimation                         [Wacht]       │
│    └── 🤖 Eliza                                                │
│                                                                 │
│ ⏳ Fase 6: Output Consolidation                  [Wacht]       │
│    └── 🤖 Diana                                                │
├─────────────────────────────────────────────────────────────────┤
│ 📊 TUSSENTIJDSE RESULTATEN                                      │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Code Metrics (Fase 1)                                        │ │
│ │ ├── Lines of Code: 145,234                                  │ │
│ │ ├── Files: 892                                              │ │
│ │ ├── Languages: Python (68%), JavaScript (25%), SQL (7%)    │ │
│ │ └── Complexity Score: 7.2/10 (Medium-High)                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Business Domeinen (Fase 2)                                   │ │
│ │ ├── 🏥 Patiëntbeheer                                        │ │
│ │ ├── 📅 Afsprakenbeheer                                      │ │
│ │ ├── 💊 Medicatiebeheer                                      │ │
│ │ ├── 📋 Dossiervoering                                       │ │
│ │ └── ... +4 meer                     [Alles bekijken]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 🔔 NOTIFICATIE INSTELLINGEN                                     │
│ ☑️ Email mij bij voltooiing                                     │
│ ☐ Stuur tussentijdse updates (per fase)                        │
├─────────────────────────────────────────────────────────────────┤
│ 💬 VRAGEN? (2)                                    [+ Vraag]    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 👤 Jan: "Worden database views meegenomen in de analyse?"   │ │
│ │ 🤖 Miguel: "Ja, SQL views worden als aparte objecten..."    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Green Paper 6-Vragen Sessie View:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 GREEN PAPER: Nieuw Klantportaal                 [↩️ Terug]   │
├─────────────────────────────────────────────────────────────────┤
│ 📊 VOORTGANG SPECIFICATIE                                       │
│ ████████████░░░░░░░░░░░░ 50%                                   │
│                                                                 │
│ Fase: Vision Questions (3/6 beantwoord)                        │
├─────────────────────────────────────────────────────────────────┤
│ ❓ VRAGEN                                                       │
│                                                                 │
│ ✅ 1. Wat is het doel van het project?           [Beantwoord]  │
│    └── "Een self-service portaal waar klanten hun..."          │
│                                                                 │
│ ✅ 2. Wie zijn de primaire gebruikers?           [Beantwoord]  │
│    └── "Zakelijke klanten (B2B), gemiddeld 50 users..."        │
│                                                                 │
│ ✅ 3. Wat zijn de kernfunctionaliteiten?         [Beantwoord]  │
│    └── "1) Dashboard met KPIs 2) Ticketsysteem 3)..."          │
│                                                                 │
│ 🔴 4. Welke integraties zijn nodig?              [Wacht op u]  │
│    └── [BEANTWOORDEN]                                          │
│                                                                 │
│ ⏳ 5. Wat zijn de performance eisen?              [Nog niet]    │
│                                                                 │
│ ⏳ 6. Wat zijn de security requirements?          [Nog niet]    │
├─────────────────────────────────────────────────────────────────┤
│ ⏱️ Na beantwoorden vraag 4 schat Peter de doorlooptijd voor    │
│ de overige vragen in en start de specification generatie.      │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AGENTS IN WACHT                                              │
│ ├── Peter: Klaar om Constitution te genereren (na vraag 6)     │
│ ├── Felix: Klaar voor Specification (HLD)                      │
│ └── Eliza: Klaar voor FP inschatting                           │
└─────────────────────────────────────────────────────────────────┘
```

**Workflow Types voor Klant:**

| Workflow | Zichtbaar voor klant | Interactie |
|----------|---------------------|------------|
| **Green Paper** | ✅ Volledig | Vragen beantwoorden |
| **Brown Paper** | ✅ Voortgang + tussenresultaten | Vragen stellen |
| **Quality Gate** | ✅ Voortgang | Alleen kijken |
| **Migration Planning** | ✅ Voortgang + tussenresultaten | Vragen beantwoorden |
| **Quickscan** | ✅ Eindresultaat (15 min) | Dashboard + PDF |

**WebSocket Events voor Live Updates:**

```typescript
// Workflow progress events
interface WorkflowProgressEvent {
  type: 'workflow_progress';
  workflow_id: string;
  workflow_type: 'green_paper' | 'brown_paper' | 'quality' | 'migration';
  stage: number;
  total_stages: number;
  stage_name: string;
  progress_percent: number;
  active_agents: string[];  // ["Felix", "Quinn"]
  stage_outputs?: Record<string, any>;  // Tussenresultaten
}

// In Refine liveProvider
liveProvider.subscribe({
  channel: `workflow:${workflowId}`,
  callback: (event: WorkflowProgressEvent) => {
    // Update UI in real-time
    setWorkflowProgress(event);
  },
});
```

---

## 9. DOCUMENTEN & AUDIT TRAIL

### 9.1 Mijn Documenten (Klant Portal)

```
📂 MIJN DOCUMENTEN
│
├── 📁 Accorderingen
│   ├── 📄 ACC-2025-0042-v1.0.pdf - Wachtwoord reset (8 FP)
│   ├── 📄 ACC-2025-0042-v2.0.pdf - Wachtwoord reset +WhatsApp (14 FP)
│   └── ...
│
├── 📁 Analyses
│   ├── 📄 Brown Paper - Patiëntenportaal - dec 2024.pdf
│   └── ...
│
├── 📁 Opleveringen
│   ├── 📄 Release Notes v1.2.0 - Sprint 12.pdf
│   └── ...
│
├── 📁 Rapportages
│   ├── 📄 FP Verbruik - januari 2025.pdf
│   └── ...
│
└── 📁 Contracten
    └── 📄 Abonnement - Goud SLA - 2025.pdf
```

### 9.2 Automatische Document Generatie

| Document | Wanneer | Automatisch |
|----------|---------|-------------|
| Accordering PDF | Bij klant akkoord | ✅ Direct |
| Analyse rapport | Na Brown/Green Paper | ✅ Direct |
| Release notes | Bij oplevering | ✅ Direct |
| FP verbruik | Einde maand | ✅ Automatisch |
| Voortgangsrapport | Configureerbaar | 🔄 Optioneel |

### 9.3 Audit Trail (Volledige historie)

Bij elke wijziging wordt vastgelegd:
- Wie (user of agent)
- Wanneer (timestamp)
- Wat (oude waarde → nieuwe waarde)
- Waarom (verplichte reden bij wijziging)

**Accordering Document bevat:**
- Versienummer
- Item beschrijving
- FP inschatting met berekening
- Onderbouwing
- Geaccordeerd door (naam)
- Datum
- Bij wijziging: reden, delta FP

---

## 10. NOTIFICATIES

### 10.1 Kanalen

- In-app (portal)
- Email
- Slack/Teams integratie

### 10.2 Configuratie

Per user per project configureerbaar:

```
Project A:
├── Nieuwe inschatting: Email + Slack
├── Status wijziging: In-app only
└── Oplevering: Alle kanalen

Project B:
├── Nieuwe inschatting: Email
└── Status wijziging: Uit
```

### 10.3 Notificatie Types

| Event | Naar wie |
|-------|----------|
| Item ingediend | Jullie (supervisor) |
| Inschatting klaar | Klant (indiener) |
| Akkoord gevraagd | Klant (accordeerder) |
| Status wijziging | Klant (indiener) |
| Blokkade | Klant + supervisor |
| Oplevering | Klant (indiener + manager) |
| FP bundel bijna op | Klant (manager/admin) |

---

## 11. SLA & PRIORITERING

### 11.1 Priority Queue

```
PRIORITY QUEUE
│
├── SLA GOUD (eerst)
│   ├── Item 1 (09:00)
│   └── Item 2 (10:00)
│
├── SLA ZILVER (daarna)
│   ├── Item 3 (08:00) ← eerder, maar lagere SLA
│   └── Item 4 (11:00)
│
└── SLA BRONS (laatst)
    └── Item 5 (07:00) ← vroegst, maar laagste SLA
```

### 11.2 SLA Levels bepalen

- Response tijd (hoe snel inschatting)
- Doorlooptijd (hoe snel opgeleverd)
- FP bundel grootte / prijs per FP

Bij gelijke SLA: First Come, First Serve

---

## 12. SUPERVISOR DASHBOARD

### 12.1 Exception-Based Management

Normale flow (geen actie nodig):
- AI classificeert met >90% confidence → verwerkt
- AI schat in, past in bundel → naar backlog
- Sprint heeft ruimte → auto-planning suggest
- Code merged → auto-status "Done"

Uitzonderingen (supervisor actie):
- 🔔 AI confidence <90% → Review nodig
- 🔔 FP > bundel beschikbaar → Beslissing nodig
- 🔔 SLA deadline nadert → Escalatie
- 🔔 Klant vraag/bezwaar → Menselijke reactie
- 🔔 Wijziging in requirements → Herclassificatie

### 12.2 Dashboard View

```
┌─────────────────────────────────────────────────────────────────┐
│ 👁️ SUPERVISOR VIEW                                              │
├─────────────────────────────────────────────────────────────────┤
│ 🔔 ACTIE NODIG (3)                                              │
│ ├── ⚠️ DigiD - Klant A - Wacht op akkoord (2 dagen)            │
│ ├── ⚠️ SSO - Peter confidence 72% - Review nodig               │
│ └── ⚠️ Klant B - SLA breach in 4 uur                           │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AGENTS ACTIVE (4)                                            │
│ ├── Peter  → SSO classificatie      [Klant A] ████░░ 60%       │
│ ├── Eliza  → Rapport FP inschatting [Klant A] ███░░░ 40%       │
│ ├── Felix  → SMS Reset spec         [Klant A] █████░ 85%       │
│ └── Marcus → API refactor review    [Klant B] ██████ 95%       │
├─────────────────────────────────────────────────────────────────┤
│ 📊 QUEUE                                                        │
│ ├── Wacht op classificatie: 4 items                             │
│ ├── Wacht op FP inschatting: 2 items                            │
│ ├── Wacht op mijn accordering: 3 items                          │
│ └── Wacht op klant akkoord: 5 items                             │
├─────────────────────────────────────────────────────────────────┤
│ 📈 VANDAAG                                                      │
│ ├── Verwerkt: 18 items                                          │
│ ├── Gemiddelde confidence: 91%                                  │
│ └── Gemiddelde doorlooptijd: 12 min                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. ROADMAP ITEMS

### 13.1 Later toe te voegen (na stabiele basis)

| Item | Beschrijving | Prioriteit |
|------|--------------|------------|
| **Auto-approve** | Bij hoge AI confidence automatisch accorderen | Na stabilisatie |
| **Simpeler intake** | Nog eenvoudiger formulier voor klant | Te evalueren |
| **Manager rapportages** | Uitgebreide KPI dashboards | Medium |

### 13.2 Technische vereisten

| Component | Techniek | Status |
|-----------|----------|--------|
| Live dashboard | WebSocket | ✅ Aanwezig |
| 9-lane Kanban | KaibanJS patterns | ✅ 82% compleet |
| FP Methodology | NESMA/IFPUG | ✅ Aanwezig |
| PDF generatie | - | 🔄 Toe te voegen |
| Multi-tenant | - | 🔄 Toe te voegen |

---

## 14. WAT IS ER AL vs NOG TE BOUWEN

### 14.1 ✅ Aanwezig

| Component | Locatie |
|-----------|---------|
| 9-Lane Kanban + auto-progression | `backend/app/api/kanban.py` |
| WebSocket live updates | `backend/app/api/websocket.py` |
| FP Work Type Classifier | `backend/app/services/fp_methodology/` |
| Agent Team (Peter, Felix, etc.) | Confucius framework |
| Green/Brown Paper workflows | `backend/app/confucius/workflows/` |
| Portal Feature Request + Voting | `backend/app/api/portal_features.py` |
| Epic/Feature/Story CRUD | `backend/app/api/epics.py`, etc. |

### 14.2 🔄 Nog te bouwen/uitbreiden

| Component | Beschrijving |
|-----------|--------------|
| Klant-specifieke portal UI | Multi-tenant views |
| FP weergave (ipv Story Points) | Aanpassing Kanban |
| Mijn Documenten | PDF opslag + viewer |
| Accordering PDF generatie | Template + data merge |
| Notificatie configuratie | Per user per project |
| SLA priority queue | Sortering aanpassen |
| Manager dashboard | KPI views |
| Impact analyse view | Bij nieuwe wens |

---

## 15. UI FRAMEWORK & TECHNOLOGIE

### 15.1 Gekozen Stack (Open Source)

| Layer | Technologie | GitHub Stars | Reden |
|-------|-------------|--------------|-------|
| **Admin Framework** | Refine | 33.2K ⭐ | Headless, backend-agnostic, RBAC built-in |
| **UI Components** | shadcn/ui | 75K+ ⭐ | Copy-paste, Tailwind, geen lock-in |
| **Styling** | Tailwind CSS | 85K+ ⭐ | Utility-first, snel, modern |
| **Backend** | Django + DRF | - | Robuust, ORM, proven |
| **Platform** | MarQed.ai | - | Agent orchestratie, workflows |

### 15.2 Waarom Refine + shadcn/ui

**Refine (https://github.com/refinedev/refine):**
```
✅ Headless - volledige UI vrijheid
✅ 306 contributors, zeer actief (weekly updates)
✅ MIT License (volledig gratis, ook commercieel)
✅ Built-in features:
   ├── Authentication & Authorization
   ├── Role-based Access Control (RBAC)
   ├── Audit logging
   ├── i18n (meertalig)
   ├── Real-time updates (WebSocket/SSE)
   └── 45+ data provider adapters
✅ Werkt met Next.js, Vite, Remix
✅ TanStack Query ingebouwd (data fetching + caching)
```

**shadcn/ui (https://ui.shadcn.com):**
```
✅ Copy-paste componenten (geen npm dependency)
✅ Tailwind CSS + Radix UI primitives
✅ Volledig aanpasbaar aan eigen design
✅ Accessible (WCAG compliant)
✅ Actieve community, weekly updates
✅ Admin template beschikbaar: github.com/satnaing/shadcn-admin
```

### 15.3 Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│ KLANT PORTAL (React + Refine + shadcn/ui)                       │
│ ├── Refine: Auth, RBAC, Data providers, Routing                │
│ ├── shadcn/ui: Buttons, Cards, Tables, Forms, Modals           │
│ ├── Tailwind CSS: Styling                                      │
│ ├── TanStack Query: Data fetching (via Refine)                 │
│ ├── Recharts: KPI grafieken                                    │
│ └── @dnd-kit: Kanban drag & drop                               │
├─────────────────────────────────────────────────────────────────┤
│ DJANGO BACKEND (REST API + BFF)                                 │
│ ├── Django REST Framework: API endpoints                       │
│ ├── Django Channels: WebSocket (live updates)                  │
│ ├── Refine Data Provider: REST adapter                         │
│ ├── Multi-tenant: Klant isolatie                               │
│ └── PostgreSQL: Database                                       │
├─────────────────────────────────────────────────────────────────┤
│ MARQED.AI PLATFORM (Integratie)                                 │
│ ├── Confucius: Agent Orchestratie                              │
│ ├── FP Methodology Engine                                      │
│ ├── Workflow Engine (Green/Brown Paper, etc.)                  │
│ └── 9-Lane Kanban Backend                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 15.4 Component Stack

```
REFINE CORE
├── @refinedev/core           → Headless admin logic
├── @refinedev/react-router   → Routing
├── @refinedev/rest           → REST data provider (Django)
└── @refinedev/react-table    → TanStack Table integration

SHADCN/UI COMPONENTEN
├── Button, Card, Dialog      → Basis UI
├── Table, DataTable          → Lijsten en overzichten
├── Form, Input, Select       → Formulieren
├── Tabs, Accordion           → Navigatie
├── Toast, Alert              → Notificaties
└── Sheet, Drawer             → Sidebars

AANVULLEND
├── Recharts                  → KPI grafieken (Manager dashboard)
├── @dnd-kit/core             → Kanban drag & drop
├── react-pdf                 → PDF viewer (Mijn Documenten)
├── date-fns                  → Datum formatting
└── zod                       → Schema validatie
```

### 15.5 Refine RBAC Mapping

Refine heeft built-in access control die direct mapt op onze rollen:

```typescript
// accessControlProvider.ts
export const accessControlProvider = {
  can: async ({ resource, action, params }) => {
    const userRole = getUserRole(); // Viewer|Indiener|Accordeerder|Manager|Admin

    const permissions = {
      Viewer: {
        project: ["list", "show"],
        epic: ["list", "show"],
        kanban: ["list"],
      },
      Indiener: {
        project: ["list", "show"],
        epic: ["list", "show"],
        feature: ["list", "show", "create", "edit", "delete"],
        story: ["list", "show", "create", "edit", "delete"],
      },
      Accordeerder: {
        // ... + approve actions
      },
      Manager: {
        // ... + dashboard, reports
      },
      Admin: {
        // ... alle rechten
      },
    };

    return { can: permissions[userRole]?.[resource]?.includes(action) };
  },
};
```

### 15.6 Project Structure

```
client-portal/
├── frontend/                         # React + Refine + shadcn
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui componenten
│   │   │   ├── kanban/              # Kanban board
│   │   │   ├── dashboard/           # KPI widgets
│   │   │   └── approval/            # Accordering componenten
│   │   │
│   │   ├── pages/                   # Refine resources
│   │   │   ├── projects/
│   │   │   │   ├── list.tsx
│   │   │   │   └── show.tsx
│   │   │   ├── epics/
│   │   │   ├── features/
│   │   │   ├── stories/
│   │   │   ├── approvals/           # Accordering pagina's
│   │   │   ├── dashboard/           # Manager KPIs
│   │   │   └── admin/               # User management
│   │   │
│   │   ├── providers/
│   │   │   ├── authProvider.ts      # Refine auth
│   │   │   ├── accessControlProvider.ts  # RBAC
│   │   │   ├── dataProvider.ts      # REST naar Django
│   │   │   └── liveProvider.ts      # WebSocket
│   │   │
│   │   └── App.tsx                  # Refine setup
│   │
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                          # Django
│   ├── portal/
│   │   ├── models.py                # Tenant, User, Permission
│   │   ├── views.py                 # REST endpoints
│   │   ├── serializers.py
│   │   └── permissions.py           # Granulaire rechten
│   │
│   ├── integrations/
│   │   └── marqed_client.py         # MarQed.ai API client
│   │
│   └── config/
│       └── settings.py
│
└── docker-compose.yml
```

### 15.7 API Integratie

**Refine Data Provider voor Django:**
```typescript
// dataProvider.ts
import { DataProvider } from "@refinedev/core";

export const dataProvider: DataProvider = {
  getList: async ({ resource, pagination, filters, sorters }) => {
    const response = await fetch(`/api/portal/${resource}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return { data: response.data, total: response.total };
  },

  getOne: async ({ resource, id }) => { /* ... */ },
  create: async ({ resource, variables }) => { /* ... */ },
  update: async ({ resource, id, variables }) => { /* ... */ },
  deleteOne: async ({ resource, id }) => { /* ... */ },
};
```

**Live Provider voor WebSocket:**
```typescript
// liveProvider.ts
export const liveProvider = {
  subscribe: ({ channel, callback }) => {
    const ws = new WebSocket(`/ws/${channel}/`);
    ws.onmessage = (event) => callback(JSON.parse(event.data));
    return { unsubscribe: () => ws.close() };
  },
};
```

### 15.8 Implementatie Roadmap

**Fase 1: Foundation**
1. Refine project setup met Vite
2. shadcn/ui componenten installeren
3. Django REST endpoints voor portal
4. Basis authenticatie (JWT)
5. Project overzicht pagina

**Fase 2: Core Portal**
1. Role-based routing (5 rollen)
2. Granulaire rechten (Epic/Feature niveau)
3. Indiener view + inschieten
4. Accordeerder view + akkoord flow
5. WebSocket live updates

**Fase 3: Advanced**
1. Manager KPI dashboard
2. Kanban board met @dnd-kit
3. PDF generatie + "Mijn Documenten"
4. Audit log
5. Admin facturatie view

---

## 16. MULTI-TENANT ARCHITECTUUR

### 16.1 Tenant Strategie

**Gekozen aanpak: Row-Level Isolation met Tenant ID**

```
┌─────────────────────────────────────────────────────────────────┐
│ MULTI-TENANT MODEL                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Klant A     │    │ Klant B     │    │ Klant C     │         │
│  │ tenant_id=1 │    │ tenant_id=2 │    │ tenant_id=3 │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SHARED DATABASE (PostgreSQL)                                ││
│  │ ┌─────────────────────────────────────────────────────────┐ ││
│  │ │ Alle tabellen hebben tenant_id kolom                    │ ││
│  │ │ Row-Level Security (RLS) op database niveau             │ ││
│  │ │ Automatische filtering via Django middleware            │ ││
│  │ └─────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Waarom Row-Level Isolation (niet schema-per-tenant):**

| Aspect | Schema-per-tenant | Row-Level (gekozen) |
|--------|-------------------|---------------------|
| Schaalbaarheid | Max ~100 tenants | Onbeperkt |
| Migraties | Per tenant uitvoeren | Eenmaal voor allen |
| Queries | Simpeler | Filter altijd nodig |
| Isolatie | Sterk | Goed (met RLS) |
| Kosten | Hoger (meer connections) | Lager |
| Cross-tenant queries | Moeilijk | Makkelijk (admin) |

### 16.2 URL Structuur

**Subdomain-based routing:**

```
https://[tenant-slug].portal.marqed.ai/

Voorbeelden:
├── ziekenhuis-noord.portal.marqed.ai/projects/
├── gemeente-amsterdam.portal.marqed.ai/kanban/
└── acme-corp.portal.marqed.ai/dashboard/

Supervisor/Admin:
└── admin.portal.marqed.ai/            → Cross-tenant view
```

**URL Mapping:**

```python
# Django URL routing
urlpatterns = [
    # Tenant-specifieke URLs (subdomain middleware bepaalt tenant)
    path('projects/', views.ProjectList.as_view()),
    path('projects/<int:pk>/', views.ProjectDetail.as_view()),
    path('kanban/', views.KanbanBoard.as_view()),

    # Admin URLs (alleen voor MarQed.ai personeel)
    path('admin/tenants/', admin_views.TenantList.as_view()),
    path('admin/tenants/<int:pk>/', admin_views.TenantDetail.as_view()),
]
```

### 16.3 Django Tenant Middleware

```python
# portal/middleware/tenant.py

class TenantMiddleware:
    """
    Extraheert tenant uit subdomain en zet in request + thread-local.

    Flow:
    1. Request binnenkomt: ziekenhuis-noord.portal.marqed.ai
    2. Middleware extraheert: "ziekenhuis-noord"
    3. Lookup in Tenant tabel
    4. Zet request.tenant = <Tenant object>
    5. Zet thread-local voor model managers
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract subdomain
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]

        # Skip voor admin subdomain
        if subdomain == 'admin':
            request.tenant = None
            request.is_admin = True
            return self.get_response(request)

        # Lookup tenant
        try:
            tenant = Tenant.objects.get(slug=subdomain, is_active=True)
            request.tenant = tenant
            request.is_admin = False

            # Zet thread-local voor automatische filtering
            set_current_tenant(tenant)

        except Tenant.DoesNotExist:
            return HttpResponseNotFound("Tenant not found")

        response = self.get_response(request)

        # Cleanup thread-local
        clear_current_tenant()

        return response
```

### 16.4 Model Design

**Base Model met Tenant:**

```python
# portal/models/base.py

class TenantAwareManager(models.Manager):
    """Manager die automatisch filtert op current tenant."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs


class TenantAwareModel(models.Model):
    """Base class voor alle tenant-specifieke models."""

    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        editable=False,
    )

    objects = TenantAwareManager()
    all_objects = models.Manager()  # Voor admin cross-tenant queries

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant = get_current_tenant()
        super().save(*args, **kwargs)
```

**Tenant Model:**

```python
# portal/models/tenant.py

class Tenant(models.Model):
    """
    Een klant/organisatie in het systeem.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)  # Voor subdomain

    # Contract info
    sla_level = models.CharField(
        max_length=20,
        choices=[('bronze', 'Brons'), ('silver', 'Zilver'), ('gold', 'Goud')],
        default='silver',
    )
    fp_bundle_monthly = models.IntegerField(default=10)
    fp_price = models.DecimalField(max_digits=10, decimal_places=2, default=300)
    overage_allowed = models.BooleanField(default=True)
    overage_price = models.DecimalField(max_digits=10, decimal_places=2, default=350)

    # Status
    is_active = models.BooleanField(default=True)
    contract_start = models.DateField()
    contract_end = models.DateField()

    # Settings
    settings = models.JSONField(default=dict)  # Tenant-specifieke config

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portal_tenant'

    def __str__(self):
        return self.name
```

**Project Model (tenant-aware):**

```python
# portal/models/project.py

class Project(TenantAwareModel):
    """Project binnen een tenant."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Actief'), ('archived', 'Gearchiveerd')],
        default='active',
    )

    # Repositories
    repositories = models.JSONField(default=list)

    # MarQed.ai platform reference
    marqed_project_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portal_project'
        unique_together = [['tenant', 'name']]
```

### 16.5 Database Row-Level Security (PostgreSQL)

**Extra beveiliging op database niveau:**

```sql
-- Enable RLS op tenant-aware tabellen
ALTER TABLE portal_project ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal_epic ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal_feature ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal_story ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal_user_project ENABLE ROW LEVEL SECURITY;

-- Policy: Users zien alleen hun tenant's data
CREATE POLICY tenant_isolation ON portal_project
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::integer);

-- Django zet session variable bij elke request
-- SET app.current_tenant_id = '123';
```

**Django Database Router:**

```python
# portal/db_router.py

class TenantRouter:
    """
    Database router die tenant context zet voor RLS.
    """

    def db_for_read(self, model, **hints):
        self._set_tenant_context()
        return 'default'

    def db_for_write(self, model, **hints):
        self._set_tenant_context()
        return 'default'

    def _set_tenant_context(self):
        tenant = get_current_tenant()
        if tenant:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET app.current_tenant_id = %s",
                    [tenant.id]
                )
```

### 16.6 API Response Filtering

**Automatische tenant filtering in DRF:**

```python
# portal/views/base.py

class TenantAwareViewSet(viewsets.ModelViewSet):
    """Base viewset met automatische tenant filtering."""

    def get_queryset(self):
        """Filter queryset op huidige tenant."""
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return qs.filter(tenant=self.request.tenant)
        return qs.none()  # Geen tenant = geen data

    def perform_create(self, serializer):
        """Zet tenant automatisch bij aanmaken."""
        serializer.save(tenant=self.request.tenant)


class ProjectViewSet(TenantAwareViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, HasProjectAccess]
```

### 16.7 Cross-Tenant Admin Access

**Supervisor dashboard (MarQed.ai personeel):**

```python
# portal/views/admin.py

class AdminViewSet(viewsets.ModelViewSet):
    """ViewSet voor MarQed.ai admins - cross-tenant toegang."""

    permission_classes = [IsAuthenticated, IsMarqedAdmin]

    def get_queryset(self):
        """Admins zien alle tenants."""
        # Gebruik all_objects manager (geen tenant filter)
        return self.queryset.model.all_objects.all()

    def list(self, request, *args, **kwargs):
        """Optioneel filteren op tenant via query param."""
        queryset = self.get_queryset()

        tenant_id = request.query_params.get('tenant')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        return super().list(request, *args, **kwargs)


class AdminProjectViewSet(AdminViewSet):
    queryset = Project.all_objects.all()
    serializer_class = AdminProjectSerializer
```

### 16.8 Refine Multi-Tenant Setup

**Frontend tenant-aware data provider:**

```typescript
// providers/dataProvider.ts

export const dataProvider: DataProvider = {
  getList: async ({ resource, pagination, filters, sorters }) => {
    // Tenant automatisch via subdomain (cookie/header)
    const response = await fetch(`/api/portal/${resource}/`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        // Tenant uit subdomain, niet handmatig meesturen
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${resource}`);
    }

    const data = await response.json();
    return {
      data: data.results,
      total: data.count,
    };
  },
  // ... andere methodes
};
```

**Tenant context in React:**

```typescript
// contexts/TenantContext.tsx

interface TenantContextType {
  tenant: Tenant | null;
  isLoading: boolean;
}

export const TenantContext = createContext<TenantContextType>({
  tenant: null,
  isLoading: true,
});

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch tenant info bij app load
    fetch('/api/portal/tenant/current/')
      .then(res => res.json())
      .then(data => {
        setTenant(data);
        setIsLoading(false);
      })
      .catch(() => {
        // Redirect naar login of error page
        window.location.href = '/login';
      });
  }, []);

  return (
    <TenantContext.Provider value={{ tenant, isLoading }}>
      {children}
    </TenantContext.Provider>
  );
}
```

### 16.9 Tenant Onboarding Flow

```
NIEUWE KLANT ONBOARDING
│
├── 1. Sales creëert Tenant in admin
│   └── admin.portal.marqed.ai/tenants/new/
│       ├── Naam: "Ziekenhuis Noord"
│       ├── Slug: "ziekenhuis-noord"
│       ├── SLA: Goud
│       ├── FP Bundel: 100/maand
│       └── Contract periode
│
├── 2. Eerste Admin user aanmaken
│   └── Email invite naar klant contact
│       └── Activatie link met tenant context
│
├── 3. Admin logt in en configureert
│   ├── Projecten aanmaken
│   ├── Repositories koppelen
│   ├── Users uitnodigen
│   └── Rollen toekennen
│
└── 4. Portal operationeel
    └── ziekenhuis-noord.portal.marqed.ai
```

### 16.10 Data Isolatie Garanties

| Laag | Mechanisme | Garantie |
|------|------------|----------|
| **URL** | Subdomain routing | Tenant bepaald uit URL |
| **Middleware** | TenantMiddleware | Request.tenant gezet |
| **ORM** | TenantAwareManager | Automatische WHERE clause |
| **Database** | PostgreSQL RLS | Extra beveiligingslaag |
| **API** | TenantAwareViewSet | Queryset filtering |
| **Cache** | Tenant-prefixed keys | `tenant:123:project:456` |
| **Files** | Tenant-prefixed paths | `s3://bucket/tenant-123/` |

**Audit van tenant leaks:**

```python
# management/commands/audit_tenant_isolation.py

class Command(BaseCommand):
    """Audit alle queries op tenant isolation."""

    def handle(self, *args, **options):
        # Check alle TenantAwareModel subclasses
        for model in apps.get_models():
            if issubclass(model, TenantAwareModel):
                # Verify tenant field exists
                assert hasattr(model, 'tenant'), f"{model} missing tenant field"

                # Verify manager filters
                qs = model.objects.all()
                assert 'tenant' in str(qs.query), f"{model} queryset not filtered"

        self.stdout.write(self.style.SUCCESS('Tenant isolation audit passed'))
```

---

## 17. SECURITY & COMPLIANCE

### 17.1 Security Architectuur Overzicht

```
┌─────────────────────────────────────────────────────────────────┐
│ SECURITY LAYERS                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── PERIMETER ───────────────────────────────────────────┐   │
│  │ • Cloudflare WAF                                         │   │
│  │ • DDoS Protection                                        │   │
│  │ • Rate Limiting (per tenant)                             │   │
│  │ • SSL/TLS 1.3 (HTTPS only)                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─── APPLICATION ─────────────────────────────────────────┐   │
│  │ • JWT Authentication (short-lived tokens)                │   │
│  │ • RBAC (5 rollen + granulaire rechten)                   │   │
│  │ • CSRF Protection                                        │   │
│  │ • Input Validation (Pydantic/Zod)                        │   │
│  │ • Output Encoding (XSS prevention)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ▼                                      │
│  ┌─── DATA ────────────────────────────────────────────────┐   │
│  │ • Row-Level Security (PostgreSQL)                        │   │
│  │ • Encryption at rest (AES-256)                           │   │
│  │ • Encryption in transit (TLS 1.3)                        │   │
│  │ • Tenant isolation (multi-layer)                         │   │
│  │ • Audit logging (immutable)                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 17.2 Authentication & Authorization

**JWT Token Strategie:**

```python
# Token configuratie
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)   # Kort voor security
REFRESH_TOKEN_LIFETIME = timedelta(days=7)      # Langer voor UX
ROTATE_REFRESH_TOKENS = True                    # Nieuwe refresh bij gebruik
BLACKLIST_AFTER_ROTATION = True                 # Oude tokens ongeldig

# Token payload
{
    "user_id": 123,
    "tenant_id": 456,
    "roles": ["indiener", "accordeerder"],
    "permissions": {
        "epic:789": ["read", "write"],
        "epic:790": ["read"]
    },
    "exp": 1704067200,
    "iat": 1704066300
}
```

**Enterprise SSO Integratie:**

| Provider | Protocol | Status |
|----------|----------|--------|
| Microsoft Entra ID | OIDC / SAML 2.0 | Fase 2 |
| Google Workspace | OIDC | Fase 2 |
| Okta | OIDC / SAML 2.0 | Fase 3 |
| Generic SAML | SAML 2.0 | Fase 3 |

**SSO Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│ SSO LOGIN FLOW                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User → Portal                                                  │
│    │                                                            │
│    ▼                                                            │
│  Portal detecteert tenant (subdomain)                           │
│    │                                                            │
│    ▼                                                            │
│  Tenant heeft SSO? ─── Nee ───► Local login form                │
│    │                                                            │
│    Ja                                                           │
│    ▼                                                            │
│  Redirect naar IdP (Microsoft/Google/Okta)                      │
│    │                                                            │
│    ▼                                                            │
│  User authenticate bij IdP                                      │
│    │                                                            │
│    ▼                                                            │
│  IdP redirect terug met SAML assertion / OIDC token             │
│    │                                                            │
│    ▼                                                            │
│  Portal valideert + mapt naar lokale user                       │
│    │                                                            │
│    ▼                                                            │
│  JWT tokens uitgegeven → Dashboard                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 17.3 Data Protection

**Encryption:**

| Data Type | At Rest | In Transit |
|-----------|---------|------------|
| Database | AES-256 (PostgreSQL TDE) | TLS 1.3 |
| File Storage | AES-256 (S3 SSE-S3) | TLS 1.3 |
| Backups | AES-256 + customer key option | TLS 1.3 |
| Secrets | AWS Secrets Manager | TLS 1.3 |
| Session Data | Encrypted Redis | TLS 1.3 |

**Key Management:**

```
KEY HIERARCHY
│
├── Master Key (AWS KMS)
│   └── Beheerd door AWS, rotatie elke 365 dagen
│
├── Tenant Data Keys
│   └── Per-tenant key, rotatie elke 90 dagen
│
└── Session Keys
    └── Per-sessie, expire met token
```

### 17.4 GDPR Compliance

**Data Subject Rights:**

| Recht | Implementatie |
|-------|---------------|
| **Right to Access** | Export functie in Admin panel |
| **Right to Rectification** | User kan eigen gegevens wijzigen |
| **Right to Erasure** | "Verwijder mijn account" flow |
| **Right to Portability** | JSON/CSV export van alle data |
| **Right to Object** | Opt-out voor marketing/analytics |

**Data Retention:**

```python
# Retentie periodes
RETENTION_POLICIES = {
    # Actieve data
    'user_data': None,              # Zolang account actief
    'project_data': None,           # Zolang project actief

    # Audit & compliance
    'audit_logs': timedelta(days=2555),      # 7 jaar (wettelijk)
    'access_logs': timedelta(days=365),      # 1 jaar
    'security_events': timedelta(days=2555), # 7 jaar

    # Na verwijdering
    'soft_deleted': timedelta(days=30),      # 30 dagen recovery
    'backup_retention': timedelta(days=90),  # 90 dagen backups

    # Anonimiseren ipv verwijderen
    'analytics': 'anonymize',        # Na 2 jaar anonimiseren
}
```

**Right to Erasure Flow:**

```
USER VRAAGT VERWIJDERING
│
├── 1. Verzoek ontvangen
│   └── Bevestig identiteit (email/2FA)
│
├── 2. Soft delete (30 dagen)
│   ├── Data gemarkeerd als "pending_deletion"
│   ├── User kan niet meer inloggen
│   └── Data niet meer zichtbaar in queries
│
├── 3. Na 30 dagen: Hard delete
│   ├── Persoonlijke gegevens verwijderd
│   ├── Content geanonimiseerd
│   └── Audit log entry (geanonimiseerd)
│
└── 4. Backups
    └── Verwijderd bij volgende backup cycle (max 90 dagen)
```

### 17.5 Audit Logging

**Wat wordt gelogd:**

```python
# Audit events
AUDIT_EVENTS = [
    # Authentication
    'user.login',
    'user.logout',
    'user.login_failed',
    'user.password_changed',
    'user.2fa_enabled',

    # Authorization
    'permission.granted',
    'permission.revoked',
    'role.assigned',
    'role.removed',

    # Data access
    'project.viewed',
    'document.downloaded',
    'export.generated',

    # Data changes
    'feature.created',
    'feature.updated',
    'feature.deleted',
    'story.created',
    'approval.granted',
    'approval.rejected',

    # Admin actions
    'user.created',
    'user.deleted',
    'tenant.settings_changed',
    'contract.modified',

    # Security events
    'suspicious_activity',
    'rate_limit_exceeded',
    'invalid_token',
]
```

**Audit Log Schema:**

```python
class AuditLog(models.Model):
    """Immutable audit log entry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Who
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT)
    actor_type = models.CharField(max_length=20)  # user, agent, system
    actor_id = models.CharField(max_length=100)
    actor_ip = models.GenericIPAddressField(null=True)
    actor_user_agent = models.TextField(blank=True)

    # What
    event = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)

    # Details
    old_value = models.JSONField(null=True)  # Voor updates
    new_value = models.JSONField(null=True)
    metadata = models.JSONField(default=dict)

    # Integrity
    checksum = models.CharField(max_length=64)  # SHA-256 of record

    class Meta:
        db_table = 'portal_audit_log'
        ordering = ['-timestamp']
        # Prevent modifications
        managed = True

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs are immutable")
        self.checksum = self._calculate_checksum()
        super().save(*args, **kwargs)
```

### 17.6 Security Headers

**Django Security Middleware:**

```python
# settings/security.py

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Voor Refine
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")   # Voor Tailwind
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "wss:")            # WebSocket

# Cookie settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

### 17.7 Vulnerability Management

**Security Scanning Pipeline:**

```
CI/CD SECURITY CHECKS
│
├── Pre-commit
│   ├── Secrets detection (git-secrets)
│   └── Dependency check (safety)
│
├── Pull Request
│   ├── SAST (Bandit voor Python)
│   ├── Dependency audit (pip-audit, npm audit)
│   └── Container scan (Trivy)
│
├── Weekly
│   ├── Full DAST scan (OWASP ZAP)
│   └── Dependency update review
│
└── Quarterly
    └── External pentest
```

**Dependency Management:**

```python
# requirements-security.txt
safety>=2.3.0           # Vulnerability scanning
bandit>=1.7.0           # SAST
pip-audit>=2.6.0        # Dependency audit

# Pre-commit config
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'portal/', '-ll']
```

### 17.8 Incident Response

**Severity Levels:**

| Level | Definitie | Response Time | Escalatie |
|-------|-----------|---------------|-----------|
| **P1 Critical** | Data breach, systeem down | < 15 min | Immediate |
| **P2 High** | Security vulnerability actief | < 1 uur | CTO |
| **P3 Medium** | Potentiële vulnerability | < 24 uur | Security lead |
| **P4 Low** | Minor security issue | < 1 week | Dev team |

**Incident Response Flow:**

```
SECURITY INCIDENT
│
├── 1. Detection & Alert
│   └── Automated monitoring / User report
│
├── 2. Triage (< 15 min)
│   ├── Severity bepalen
│   ├── Scope inschatten
│   └── Team activeren
│
├── 3. Containment
│   ├── Getroffen systemen isoleren
│   ├── Credentials roteren indien nodig
│   └── Forensic snapshot maken
│
├── 4. Investigation
│   ├── Root cause analysis
│   ├── Impact assessment
│   └── Evidence verzamelen
│
├── 5. Remediation
│   ├── Vulnerability fixen
│   ├── Patches deployen
│   └── Monitoring verhogen
│
├── 6. Recovery
│   ├── Services herstellen
│   ├── Data valideren
│   └── Stakeholders informeren
│
└── 7. Post-mortem
    ├── Timeline documenteren
    ├── Lessons learned
    └── Process improvements
```

### 17.9 Compliance Certifications (Roadmap)

| Certification | Status | Target |
|---------------|--------|--------|
| **SOC 2 Type I** | Gepland | Q2 2026 |
| **SOC 2 Type II** | Gepland | Q4 2026 |
| **ISO 27001** | Assessment | 2027 |
| **NEN 7510** | Evaluatie | TBD (voor zorg) |

---

## 18. COMMENTS & ATTACHMENTS

### 18.1 Comment Data Model

```python
# portal/models/comment.py

class Comment(TenantAwareModel):
    """
    Discussie comment op elk entity type.

    Supports:
    - Threaded replies (parent_id)
    - Rich text (markdown)
    - Mentions (@user)
    - Attachments
    """

    # Polymorphic reference
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('feature', 'Feature'),
            ('story', 'Story'),
            ('approval', 'Approval'),
            ('bug', 'Bug'),
        ],
    )
    entity_id = models.IntegerField()

    # Threading
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
    )

    # Author
    author_type = models.CharField(
        max_length=20,
        choices=[('user', 'User'), ('agent', 'AI Agent')],
    )
    author_user = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL,
    )
    author_agent = models.CharField(max_length=50, blank=True)  # "Peter", "Felix"

    # Content
    content = models.TextField()  # Markdown supported
    content_html = models.TextField(blank=True)  # Pre-rendered HTML

    # Mentions (for notifications)
    mentions = models.JSONField(default=list)  # [{"type": "user", "id": 123}]

    # Status
    is_internal = models.BooleanField(default=False)  # Only MarQed team sees
    is_resolved = models.BooleanField(default=False)  # For questions

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True)  # Explicit edit timestamp

    class Meta:
        db_table = 'portal_comment'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['parent_id']),
        ]

    def save(self, *args, **kwargs):
        # Pre-render markdown
        self.content_html = markdown_to_html(self.content)
        # Extract mentions
        self.mentions = extract_mentions(self.content)
        super().save(*args, **kwargs)
```

### 18.2 Attachment Model

```python
# portal/models/attachment.py

class Attachment(TenantAwareModel):
    """
    File attachment voor comments of entities.

    Security:
    - Virus scanning op upload
    - File type whitelist
    - Size limits per tenant/role
    """

    # Link to comment or entity
    comment = models.ForeignKey(
        'Comment',
        null=True,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    # Direct entity attachment (zonder comment)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.IntegerField(null=True)

    # File info
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)  # MIME type
    file_size = models.IntegerField()  # bytes
    file_hash = models.CharField(max_length=64)  # SHA-256

    # Storage
    storage_path = models.CharField(max_length=500)  # S3 path
    storage_url = models.URLField(blank=True)  # Pre-signed URL (temporary)

    # Security
    virus_scanned = models.BooleanField(default=False)
    virus_scan_result = models.CharField(max_length=50, blank=True)
    virus_scanned_at = models.DateTimeField(null=True)

    # Uploader
    uploaded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_attachment'

    @property
    def is_image(self):
        return self.file_type.startswith('image/')

    @property
    def is_safe(self):
        return self.virus_scanned and self.virus_scan_result == 'clean'
```

### 18.3 File Upload Configuratie

```python
# File restrictions
ATTACHMENT_CONFIG = {
    'allowed_types': [
        # Images
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/webp',

        # Documents
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

        # Text
        'text/plain',
        'text/csv',
        'text/markdown',

        # Archives (for logs, etc.)
        'application/zip',
    ],

    'max_file_size': {
        'default': 10 * 1024 * 1024,      # 10 MB
        'image': 5 * 1024 * 1024,          # 5 MB
        'admin': 50 * 1024 * 1024,         # 50 MB voor admins
    },

    'max_files_per_comment': 5,
    'max_total_per_entity': 20,

    # Storage
    'storage_backend': 's3',
    'bucket': 'marqed-portal-attachments',
    'path_template': 'tenant-{tenant_id}/{entity_type}/{entity_id}/{filename}',
}
```

### 18.4 Virus Scanning

```python
# services/virus_scanner.py

class VirusScanner:
    """
    Virus scanning via ClamAV of cloud service.
    """

    async def scan_file(self, file_path: str) -> ScanResult:
        """Scan file for malware."""

        # Option 1: ClamAV (self-hosted)
        if settings.VIRUS_SCANNER == 'clamav':
            result = await self._scan_clamav(file_path)

        # Option 2: AWS GuardDuty / S3 Malware Protection
        elif settings.VIRUS_SCANNER == 'aws':
            result = await self._scan_aws(file_path)

        return result

    def _scan_clamav(self, file_path: str) -> ScanResult:
        """Scan via ClamAV daemon."""
        cd = clamd.ClamdUnixSocket()
        result = cd.scan(file_path)

        if result is None:
            return ScanResult(status='clean')

        if result[file_path][0] == 'FOUND':
            return ScanResult(
                status='infected',
                threat=result[file_path][1]
            )

        return ScanResult(status='clean')
```

### 18.5 Comment UI Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│ 💬 DISCUSSIE (4)                                    [Reageren +]│
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 👤 Jan de Vries                              14 jan, 10:32  │ │
│ │ ──────────────────────────────────────────────────────────  │ │
│ │ Kunnen we hier ook een terugval naar wachtwoord inbouwen    │ │
│ │ als DigiD niet beschikbaar is?                              │ │
│ │                                                             │ │
│ │ 📎 screenshot.png (234 KB)                    [Download]    │ │
│ │                                                             │ │
│ │ [Reageren]                                                  │ │
│ │                                                             │ │
│ │   ┌───────────────────────────────────────────────────────┐ │ │
│ │   │ 🤖 Peter (AI)                         14 jan, 10:45   │ │ │
│ │   │ ────────────────────────────────────────────────────  │ │ │
│ │   │ Goed punt! Ik heb dit toegevoegd als acceptatie-      │ │ │
│ │   │ criterium:                                            │ │ │
│ │   │                                                       │ │ │
│ │   │ > AC5: Bij DigiD storing kan gebruiker terugvallen    │ │ │
│ │   │ > naar wachtwoord + 2FA login                         │ │ │
│ │   │                                                       │ │ │
│ │   │ [Reageren]  [✓ Markeer als opgelost]                  │ │ │
│ │   └───────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │   ┌───────────────────────────────────────────────────────┐ │ │
│ │   │ 👤 Jan de Vries                       14 jan, 11:02   │ │ │
│ │   │ ────────────────────────────────────────────────────  │ │ │
│ │   │ Perfect, @Klaas kun jij dit accorderen?               │ │ │
│ │   └───────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔒 INTERN (alleen MarQed team)               15 jan, 09:00  │ │
│ │ ──────────────────────────────────────────────────────────  │ │
│ │ 👤 Supervisor: Let op, DigiD heeft nieuwe test-omgeving.   │ │
│ │ Zie: https://confluence.internal/digid-test                │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Nieuw comment...                                            │ │
│ │                                                             │ │
│ │ [B] [I] [Link] [Code] [@mention] [📎 Bijlage]              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [PLAATSEN]                                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 18.6 Notificaties bij Comments

**Trigger → Notificatie:**

| Event | Naar wie | Kanalen |
|-------|----------|---------|
| Nieuw comment | Entity owner + watchers | In-app, Email |
| Reply op jouw comment | Comment author | In-app, Email |
| @mention | Mentioned user | In-app, Email, Slack |
| Vraag beantwoord door AI | Vraagsteller | In-app |
| Comment gemarkeerd opgelost | Thread participants | In-app |

**Notificatie batching:**

```python
# Voorkom notification spam
NOTIFICATION_CONFIG = {
    'batch_window': timedelta(minutes=5),   # Groepeer binnen 5 min
    'max_per_hour': 20,                     # Max 20 emails/uur
    'digest_threshold': 5,                  # Bij >5: stuur digest
}
```

---

## 19. APPENDIX

### 19.1 Gerelateerde Documenten

- [9-Lane Kanban Implementation Plan](/.serena/memories/9-lane-kanban-implementation-plan.md)
- [FP Methodology](./function-point-methodology.md)
- [Kanban System Architecture](./kanban-system.md)
- [Confucius Orchestrator](./confucius-orchestrator-integration-plan.md)

### 19.2 API Endpoints Overzicht

**Klant Portal (Django):**
- `POST /api/portal/features/submit` - Wens/bug inschieten
- `GET /api/portal/features/{id}` - Item details
- `POST /api/portal/features/{id}/approve` - Akkoord geven
- `GET /api/portal/documents` - Mijn documenten
- `GET /api/portal/users` - User management
- `POST /api/portal/permissions` - Rechten beheer
- `GET /api/portal/comments` - Comments ophalen
- `POST /api/portal/comments` - Comment plaatsen
- `POST /api/portal/attachments` - Bijlage uploaden
- `GET /api/portal/workflows` - Lopende workflows
- `GET /api/portal/workflows/{id}` - Workflow details

**Multi-tenant:**
- `GET /api/portal/tenant/current` - Huidige tenant info
- `GET /api/admin/tenants` - Alle tenants (admin only)
- `POST /api/admin/tenants` - Tenant aanmaken

**Kanban (MarQed.ai):**
- `GET /api/kanban/board` - Board items
- `GET /api/kanban/stats` - Statistieken
- `PATCH /api/kanban/{id}/move` - Item verplaatsen

**Workflows (MarQed.ai):**
- `POST /confucius/workflows/green-paper/start`
- `POST /confucius/workflows/brown-paper/start`
- `POST /confucius/workflows/quality/start`
- `POST /api/quickscan/scan`

**WebSocket (MarQed.ai):**
- `WS /ws/kanban/{project_id}` - Live kanban updates
- `WS /ws/workflow/{workflow_id}` - Workflow progress

---

*Document gegenereerd: 2026-01-15*
*Versie: 3.0 - Met multi-tenant, security, comments en workflow progress views*
