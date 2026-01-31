# MarQed.ai — Client Service Journey

**Week:** 162 (2026-01-31)
**Status:** Definitief
**Type:** Service Journey & Dienstenportfolio

---

## 1. Overzicht

Dit document beschrijft de volledige **client service journey** van MarQed.ai: van intake tot facturatie. De journey loopt over vier parallelle streams (swim-lanes) die samenwerken via gedefinieerde hand-offs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLIENT SERVICE JOURNEY                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Stream 1: KLANT KANAAL         Klant-acties (email, portal, review)        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Stream 2: OPENCLAW / ADMIN     Sync-bot + FlowInquiry administratie        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Stream 3: MARQED.AI            Technische executie (agents, pipelines)     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Stream 4: FACTURATIE           Abonnement, FP-afschrijving, rapportage     │
│                                                                             │
│  ──────►  Fase I  ──►  Fase II  ──►  Fase III  ──►  Fase IV  ──►  Fase V  │
│           Intake      Offerte     Uitvoering     Oplevering    Facturatie   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fase I: Intake (gratis)

```
Stream 1  KLANT         ●───► Dient vraag in via email of portal
                               │
Stream 2  OPENCLAW       ◄────┘ Ontvangt, classificeert, maakt ticket
                               │  in FlowInquiry (type, urgentie, SLA-tier)
                               │
Stream 3  MARQED.AI      ◄────┘ Draait Quickscan (15 min, automatisch, gratis)
                               │  → tech stack, LOC, first impression
                               │
Stream 4  FACTURATIE           Ticket aangemaakt, SLA-klok start
                               Geen kosten (Quickscan is gratis)
```

### Hand-offs

| Van | Naar | Trigger | Data |
|-----|------|---------|------|
| Klant | OpenClaw | Email/portal submit | Vraag + eventueel broncode/URL |
| OpenClaw | FlowInquiry | Classificatie compleet | Ticket met type, urgentie, SLA |
| OpenClaw | MarQed.ai | Ticket aangemaakt | Workflow start via REST API |

---

## 3. Fase II: Offerte & Accordering

```
Stream 3  MARQED.AI      ●───► Quickscan-resultaat beschikbaar:
                               │  tech stack, complexity, LOC, security,
                               │  effort-schatting (FP)
                               │
Stream 2  OPENCLAW       ◄────┘ Stuurt Quickscan-rapport naar klant
                               │
Stream 1  KLANT          ◄────┘ Ontvangt rapport + FP-schatting voor vervolg
                               │  (Brown Paper / Green Paper / Migration / etc.)
                               │
                          ●───► Accordeert → FP worden gereserveerd uit bundel
                               │  (10 / 25 / 50 / 100 FP abonnement)
                               │
Stream 2  OPENCLAW       ◄────┘ Accordering vastgelegd in FlowInquiry
                               │
Stream 4  FACTURATIE     ◄────┘ FP-reservering geregistreerd
```

### Hand-offs

| Van | Naar | Trigger | Data |
|-----|------|---------|------|
| MarQed.ai | OpenClaw | Quickscan klaar | Rapport (tech stack, complexity, FP-schatting) |
| OpenClaw | Klant | Rapport beschikbaar | PDF/portal link met Quickscan-resultaat |
| Klant | OpenClaw | Accordering | Goedkeuring + gekozen diensttype |
| OpenClaw | FlowInquiry | Accordering ontvangen | Ticket update + FP-reservering |

---

## 4. Fase III: Uitvoering

```
Stream 2  OPENCLAW       ●───► Start MarQed.ai workflow via REST API
                               │
Stream 3  MARQED.AI      ◄────┘ Uitvoering afhankelijk van diensttype
                               │  (zie 4.1 t/m 4.5 hieronder)
                               │
Stream 2  OPENCLAW             Pollt status, update FlowInquiry + Portal
                               │
Stream 4  FACTURATIE           SLA-monitoring:
                               escalatie bij 75% / 90% / 100% deadline
```

### 4.1 Brown Paper Analysis (legacy naar modernisatie)

Volledige analyse van een bestaand legacy systeem voor modernisatieplanning.

| Stap | Agent(s) | Activiteit | Output |
|------|----------|------------|--------|
| 1 | **Miguel** | Code understanding | Dependency graphs, layered analysis |
| 2 | **Peter + Betty** | Domain extraction | Business domeinen, bounded contexts |
| 3 | **Vicky + Peter** | User journey extraction | UI flows, persona's, gebruikersscenario's |
| 4 | **Peter** | Story extraction | Epics, features, user stories |
| 5 | **Felix + Quinn + Marcus** | Deep extraction (LLM council) | Multi-agent consensus review |
| 6 | **Eliza** | FP-schatting | NESMA/IFPUG functiepuntanalyse |
| 7 | **Diana** | Output consolidation | Eindrapport |

### 4.2 Green Paper (greenfield)

Nieuwbouw-specificatie voor een applicatie die nog niet bestaat.

| Stap | Agent(s) | Activiteit | Output |
|------|----------|------------|--------|
| 1 | — | Vision definition | 6 strategische vragen beantwoord |
| 2 | **Peter** | Requirements/constitution | Functionele en niet-functionele eisen |
| 3 | **Vicky** | UI/UX specifications | Wireframes, user flows, design system |
| 4 | **Felix** | System architecture | Technische architectuur, stack keuze |
| 5 | **Paul** | Implementation roadmap | Fasering, milestones, afhankelijkheden |
| 6 | **Quinn** | Quality review | Kwaliteitsvalidatie op alle deliverables |

### 4.3 Migration Planning

Strategisch migratieplan voor platform- of technologietransities.

| Stap | Agent(s) | Activiteit | Output |
|------|----------|------------|--------|
| 1 | — | 8 strategische vragen (Q1-Q8) | Migratiecontext vastgelegd |
| 2 | **Miguel** | Complexity & risk assessment | Risicomatrix, complexiteitsanalyse |
| 3 | **Peter** | Comprehensive spec | Volledige migratiespecificatie |
| 4 | **Felix** | Epic/feature/story hierarchy | Gestructureerde backlog |
| 5 | **Quinn** | Quality assurance | Migratieplan gevalideerd |

### 4.4 Quality Audit

Diepgaande kwaliteitsanalyse van een bestaande codebase.

| Stap | Agent(s) | Activiteit | Output |
|------|----------|------------|--------|
| 1 | **Miguel** | Quality scanners | Security, code smell, complexity metrics |
| 2 | **Miguel** | Metrics analysis | Trendanalyse, hotspots, technische schuld |
| 3 | **Quinn** | Quality gates | Pass/fail op 7 quality dimensions |
| 4 | **Marcus** | Remediation planning | Verbeterplan met prioritering |
| 5 | **Tessa** | Testing validation | Testdekking, test gaps, aanbevelingen |

### 4.5 New Feature / Bug / Maintenance / Enhancement

Doorlopend werk via het 9-lane kanban systeem.

```
┌──────────┐   ┌──────────┐   ┌─────────┐   ┌───────┐   ┌──────┐   ┌───────────┐   ┌──────┐
│ Backlog  │──►│ Analysis │──►│ Planned │──►│ Build │──►│ Test │──►│ In Review │──►│ Done │
└──────────┘   └──────────┘   └─────────┘   └───────┘   └──────┘   └───────────┘   └──────┘
                    │              │             │           │            │
                    ▼              ▼             ▼           ▼            ▼
               Quality gate   Quality gate  Quality gate Quality gate Quality gate
               (42 regels)    (42 regels)   (42 regels) (42 regels)  (42 regels)
```

**Kenmerken:**
- Quality gates bij **elke lane-transitie** (42+ validatieregels)
- **PIV-loop:** Plan → Implement → Validate (max 3 iteraties per item)
- Automatische escalatie naar **Human Needed** na 3 failed retries
- Event-driven agent triggers bij lane entry
- Hybrid agent selection (tags → AI → Human)
- Definition of Done (DoD) per lane

---

## 5. Fase IV: Oplevering & Accordering

```
Stream 3  MARQED.AI      ●───► Resultaat klaar, quality gates passed
                               │
Stream 2  OPENCLAW       ◄────┘ Stuurt resultaat naar klant
                               │  (portal + notificatie)
                               │
Stream 1  KLANT          ◄────┘ Reviewt resultaat
                               │
                          ●───► Accordeert oplevering
                               │  → FP definitief afgeschreven van bundel
                               │
Stream 2  OPENCLAW       ◄────┘ FlowInquiry ticket → DONE
                               │  Geaccordeerde FP vastgelegd
                               │
                          ●───► Stuurt korte ticket-evaluatie naar klant
                               │  (3-5 vragen, optioneel maar gestimuleerd)
                               │
Stream 1  KLANT          ◄────┘ Vult evaluatie in (optioneel)
                               │  → score + feedback opgeslagen
                               │
Stream 4  FACTURATIE     ◄────┘ FP definitief afgeschreven
```

### Hand-offs

| Van | Naar | Trigger | Data |
|-----|------|---------|------|
| MarQed.ai | OpenClaw | Quality gates passed | Eindresultaat + quality scores |
| OpenClaw | Klant | Resultaat beschikbaar | Portal link + notificatie |
| Klant | OpenClaw | Accordering oplevering | Goedkeuring |
| OpenClaw | FlowInquiry | Klant akkoord | Ticket → DONE, FP afgeschreven |
| OpenClaw | Klant | Ticket → DONE | Ticket-evaluatie (3-5 vragen) via portal/email |
| Klant | FlowInquiry | Evaluatie ingevuld | Tevredenheidsscore + feedback |

---

## 6. Fase V: Facturatie (maandelijks)

```
Stream 4  FACTURATIE     ●───► Einde maand: automatische rapportage
                               │
Stream 2  OPENCLAW       ◄────┘ Genereert maandrapport uit FlowInquiry data
                               │
Stream 1  KLANT          ◄────┘ Ontvangt factuur + rapportage
```

### Maandrapport bevat

| Element | Bron |
|---------|------|
| Uitgevoerde werkzaamheden (per ticket) | FlowInquiry |
| Type dienst per ticket (Brown Paper, Migration, etc.) | FlowInquiry |
| Geaccordeerde functiepunten per ticket | FlowInquiry |
| Resterende FP in bundel | FlowInquiry |
| SLA-performance (doorlooptijden, escalaties) | FlowInquiry + MarQed.ai |
| Quality scores (uit MarQed.ai quality gates) | MarQed.ai REST API |
| Klanttevredenheidsscore (gemiddeld per ticket) | FlowInquiry (ticket-evaluaties) |
| NPS-score (uit periodiek onderzoek) | FlowInquiry (applicatie-reviews) |

### Factuurstructuur

- **Vast:** Maandelijks abonnementsbedrag (bundel)
- **Variabel:** Eventuele extra FP buiten bundel (meerwerk)

---

## 7. Diensten-overzicht

| Dienst | Beschrijving | Typische FP | Doorlooptijd | Agents | Output |
|--------|-------------|-------------|--------------|--------|--------|
| **Quickscan** | Snelle analyse van tech stack, complexity, LOC | Gratis | 15 min | Miguel (automatisch) | Quickscan-rapport |
| **Brown Paper Analysis** | Legacy systeem analyse voor modernisatie | 15-40 FP | 2-5 dagen | Miguel, Peter, Betty, Vicky, Felix, Quinn, Marcus, Eliza, Diana | Modernisatierapport |
| **Green Paper** | Greenfield specificatie (nieuwbouw) | 10-30 FP | 2-4 dagen | Peter, Vicky, Felix, Paul, Quinn | Volledige specificatie |
| **Migration Planning** | Platform/technologie migratieplan | 10-25 FP | 2-4 dagen | Miguel, Peter, Felix, Quinn | Migratieplan + backlog |
| **Quality Audit** | Diepgaande kwaliteitsanalyse | 5-15 FP | 1-3 dagen | Miguel, Quinn, Marcus, Tessa | Kwaliteitsrapport + verbeterplan |
| **New Feature** | Nieuwe functionaliteit implementeren | 3-15 FP | 1-5 dagen | Via 9-lane kanban | Werkende feature + tests |
| **Bug Fix** | Fout oplossen in bestaande code | 1-5 FP | 4h-2 dagen | Via 9-lane kanban | Fix + regressietest |
| **Maintenance** | Onderhoud, updates, dependency management | 1-5 FP | 4h-2 dagen | Via 9-lane kanban | Bijgewerkte codebase |
| **Enhancement** | Verbetering van bestaande functionaliteit | 2-10 FP | 1-3 dagen | Via 9-lane kanban | Verbeterde feature + tests |

---

## 8. Abonnementsmodel

| Bundel | FP/maand | Doelgroep | Typisch gebruik |
|--------|----------|-----------|-----------------|
| **Starter** | 10 FP | Kleine applicaties, onderhoud | 2-3 bug fixes + 1 kleine feature |
| **Professional** | 25 FP | Middelgrote projecten | 1 Brown Paper OF meerdere features |
| **Business** | 50 FP | Meerdere applicaties | Brown Paper + doorlopend onderhoud |
| **Enterprise** | 100 FP | Grote portfolio's | Meerdere analyses + continu development |

### Hoe het werkt

1. Klant kiest een bundel (maandelijks abonnement)
2. Per opdracht worden FP geschat (na Quickscan)
3. Klant accordeert → FP worden gereserveerd uit bundel
4. Na oplevering + klantaccordering → FP definitief afgeschreven
5. Ongebruikte FP vervallen niet (rollover binnen kwartaal)
6. Extra FP buiten bundel: meerwerktarief op factuur

---

## 9. Roadmap-diensten (gepland)

Diensten die op de roadmap staan en later aan het portfolio worden toegevoegd:

| Fase | Dienst/Feature | Beschrijving | Impact op Journey |
|------|---------------|--------------|-------------------|
| **Fase 32** | Ralph Wiggum + mq integratie | Uitgebreide agent orchestratie | Meer diensten parallel uitvoerbaar |
| **Fase 51** | Multi-tenant platform | Meerdere klanten parallel bedienen | Schaalbaar naar meerdere organisaties |
| **Fase 60** | Observability (OTLP/Langfuse) | Telemetrie en monitoring | Real-time inzicht in uitvoering |
| **Fase 61** | Progress dashboard + per-ticket cost tracking | Live voortgang en kostentracking | Klant ziet real-time status + kosten |
| **Fase 62** | Conversational intake (Epic Mode) | Interactieve intake via conversatie | Fase I wordt rijker en interactiever |
| **Fases 60-64** | Tracer/BART integratie | Traceability en analyse tooling | Diepere audit trail en compliance |
| **Fase 6 (gap)** | C9 Uniface/Proc support | Legacy Uniface/Proc taalondersteuning | Nieuwe klantgroep (Uniface migraties) |

---

## 10. Swim-Lane Samenvatting

```
          Fase I          Fase II           Fase III          Fase IV         Fase V
          INTAKE          OFFERTE           UITVOERING        OPLEVERING      FACTURATIE
          (gratis)        & AKKOORD                           & AKKOORD       (maandelijks)

KLANT     ●─Vraag──────► ◄─Rapport────────                  ◄─Resultaat──► ◄─Factuur
          indienen        Accordeert───►                      Accordeert───►  + rapport

OPENCLAW  ◄─Classificeer  Stuurt rapport   Start workflow    Stuurt result   Genereert
          Maakt ticket─►  Legt akkoord     Pollt status──►   Ticket→DONE     maandrapport
                          vast──────────►  Update portal

MARQED    ◄─Quickscan──► ◄─Resultaat       ◄─Uitvoering──►  Quality gates
          (15 min)        beschikbaar       (zie 4.1-4.5)    passed────────►

FACTUR.   SLA-klok start  FP-reservering   SLA-monitoring    FP definitief   Factuur
                          geregistreerd    75%/90%/100%      afgeschreven    verstuurd

──────────────────────────────────────────────────────────────────────────────────────
FEEDBACK  ◄─Quickscan─── ◄─Milestone────  ◄─Escalatie────  ◄─Ticket-eval─  ◄─NPS/CSAT
LOOP       conversie-     feedback         recovery          na akkoord      in rapport
           peiling                          peiling
```

---

## 11. Klanttevredenheidsonderzoeken

MarQed.ai meet klanttevredenheid op meerdere momenten in de journey via geautomatiseerde onderzoeken. Alle onderzoeken worden verstuurd door OpenClaw (via portal of email) en resultaten landen in FlowInquiry voor tracking en rapportage.

### 11.1 Kern-onderzoeken (structureel)

| Type | Trigger | Moment in Journey | Lengte | Doel |
|------|---------|-------------------|--------|------|
| **Ticket-evaluatie** | Na Fase IV (oplevering geaccordeerd) | Per afgerond ticket | Kort (3-5 vragen) | Directe feedback op kwaliteit en doorlooptijd |
| **Applicatie-review** | Periodiek (per kwartaal) | Doorlopend | Langer (10-15 vragen) | Totaalbeeld per applicatie/portfolio |
| **Onboarding-peiling** | Na eerste ticket afgerond | Bij nieuwe klanten | Kort (5-7 vragen) | Verwachtingen vs. realiteit |
| **Exit-onderzoek** | Bij opzegging/niet-verlenging | Bij vertrek | Kort (5-7 vragen) | Vertrekreden, verbeterpunten |

#### 11.1.1 Ticket-evaluatie

**Trigger:** Automatisch na Fase IV — zodra klant de oplevering accordeert en het ticket status DONE krijgt.
**Verzending:** OpenClaw stuurt evaluatielink via portal-notificatie + email.
**Resultaten:** FlowInquiry (gekoppeld aan ticket) + maandrapport + SLA-dashboard.

**Vragen:**

1. Hoe tevreden bent u over de **kwaliteit** van het opgeleverde resultaat? *(1-5 sterren)*
2. Hoe tevreden bent u over de **doorlooptijd** van dit ticket? *(1-5 sterren)*
3. Was de **communicatie** tijdens het traject duidelijk en tijdig? *(1-5 sterren)*
4. Zou u MarQed.ai **aanbevelen** aan een collega? *(0-10 NPS)*
5. Heeft u nog **opmerkingen of suggesties**? *(open tekstveld)*

**Score-gebruik:** Gemiddelde per ticket in maandrapport. NPS-vraag voedt kwartaal-NPS. Scores < 3 triggeren automatisch een follow-up door OpenClaw.

#### 11.1.2 Applicatie-review

**Trigger:** Periodiek per kwartaal, voor elke applicatie/portfolio waarvoor actief werk wordt uitgevoerd.
**Verzending:** OpenClaw stuurt review-uitnodiging via portal + email aan primaire contactpersoon.
**Resultaten:** FlowInquiry (portfolio-niveau) + kwartaalrapport.

**Vragen:**

1. Hoe tevreden bent u over de **algehele kwaliteit** van het werk aan [applicatie]? *(1-5 sterren)*
2. Hoe ervaart u de **beschikbaarheid en responsiviteit** van het team? *(1-5 sterren)*
3. In hoeverre sluit het geleverde werk aan bij uw **verwachtingen en prioriteiten**? *(1-5 sterren)*
4. Hoe beoordeelt u de **proactieve communicatie** over voortgang en risico's? *(1-5 sterren)*
5. Hoe ervaart u de **FP-besteding** in verhouding tot de geleverde waarde? *(1-5 sterren)*
6. Zijn er **knelpunten of frustraties** die u wilt benoemen? *(open tekstveld)*
7. Welke **verbeteringen** zou u het liefst zien in het komende kwartaal? *(open tekstveld)*
8. Hoe waarschijnlijk is het dat u MarQed.ai **aanbeveelt** aan anderen? *(0-10 NPS)*
9. Hoe beoordeelt u de **quality gate rapportages** die u ontvangt? *(1-5 sterren)*
10. Heeft u behoefte aan **andere of aanvullende diensten**? *(open tekstveld)*

**Score-gebruik:** Portfolio-gemiddelde in kwartaalrapport. NPS-tracking over tijd. Input voor roadmap-prioritering.

#### 11.1.3 Onboarding-peiling

**Trigger:** Automatisch nadat het eerste ticket van een nieuwe klant is afgerond en geaccordeerd.
**Verzending:** OpenClaw stuurt via portal + email, 1 werkdag na eerste ticket-accordering.
**Resultaten:** FlowInquiry (klant-niveau) + onboarding-metrics dashboard.

**Vragen:**

1. Hoe ervaarde u het **intake-proces** (van eerste contact tot Quickscan)? *(1-5 sterren)*
2. Was de **Quickscan** informatief en waardevol? *(1-5 sterren)*
3. Was de **offerte/FP-schatting** duidelijk en transparant? *(1-5 sterren)*
4. Hoe verliep de **communicatie** tijdens uw eerste opdracht? *(1-5 sterren)*
5. Komt het eindresultaat overeen met uw **verwachtingen** vooraf? *(1-5 sterren)*
6. Wat kunnen we verbeteren aan de **onboarding-ervaring**? *(open tekstveld)*
7. Zou u MarQed.ai **aanbevelen** op basis van deze eerste ervaring? *(0-10 NPS)*

**Score-gebruik:** Onboarding-conversie tracking. Identificatie van friction points in Fase I-II. Scores < 3 triggeren persoonlijk contact door OpenClaw.

#### 11.1.4 Exit-onderzoek

**Trigger:** Bij opzegging van abonnement of niet-verlenging na kwartaaleinde.
**Verzending:** OpenClaw stuurt via email, binnen 2 werkdagen na opzegging/niet-verlenging.
**Resultaten:** FlowInquiry (klant-niveau) + churn-analyse dashboard.

**Vragen:**

1. Wat is de **belangrijkste reden** voor uw vertrek? *(multiple choice: prijs, kwaliteit, snelheid, behoefte vervallen, andere aanbieder, anders)*
2. Hoe tevreden was u **overall** over de samenwerking? *(1-5 sterren)*
3. Was er iets dat we hadden kunnen doen om u te **behouden**? *(open tekstveld)*
4. Zou u in de toekomst opnieuw **overwegen** om MarQed.ai in te schakelen? *(ja/misschien/nee)*
5. Heeft u nog **feedback** die ons kan helpen verbeteren? *(open tekstveld)*

**Score-gebruik:** Churn-analyse en retentie-strategie. Categorisatie van vertrekredenen. Input voor product- en procesverbeteringen.

### 11.2 Event-driven onderzoeken (situationeel)

| Type | Trigger | Moment in Journey | Lengte | Doel |
|------|---------|-------------------|--------|------|
| **Quickscan-conversie** | Na Quickscan, klant gaat niet door | Fase I→II transitie | Kort (3 vragen) | Conversie-optimalisatie |
| **Escalatie-recovery** | Na Human Needed afhandeling | Fase III (na escalatie) | Kort (3-4 vragen) | Recovery-ervaring meten |
| **SLA-breach feedback** | Na SLA-overschrijding afgehandeld | Fase III/IV | Kort (3-4 vragen) | Communicatie en vertrouwensherstel |
| **Milestone-feedback** | Na deelopleveringen (Brown Paper, Migration) | Fase III (tussentijds) | Kort (3-5 vragen) | Bijsturen vóór eindresultaat |

#### 11.2.1 Quickscan-conversie

**Trigger:** Wanneer een klant na de gratis Quickscan (Fase I) niet doorgaat naar Fase II (offerte/accordering).
**Verzending:** OpenClaw stuurt via email, 3 werkdagen na Quickscan zonder vervolg.
**Resultaten:** FlowInquiry (ticket-niveau) + conversie-dashboard.

**Vragen:**

1. Waarom heeft u besloten **niet door te gaan** na de Quickscan? *(multiple choice: prijs, timing, scope, intern besluit, andere aanbieder, anders)*
2. Was het **Quickscan-rapport** nuttig en begrijpelijk? *(1-5 sterren)*
3. Is er iets waarmee we u alsnog kunnen **helpen**? *(open tekstveld)*

**Score-gebruik:** Conversie-optimalisatie van Fase I→II. Verbetering van Quickscan-rapport en pricing-communicatie.

#### 11.2.2 Escalatie-recovery

**Trigger:** Na afhandeling van een Human Needed escalatie in Fase III (wanneer automatische verwerking faalt na 3 PIV-iteraties).
**Verzending:** OpenClaw stuurt via portal + email, na succesvolle afhandeling van de escalatie.
**Resultaten:** FlowInquiry (ticket-niveau) + escalatie-metrics.

**Vragen:**

1. Hoe ervaarde u de **snelheid** waarmee de escalatie werd opgepakt? *(1-5 sterren)*
2. Was de **communicatie** over de escalatie duidelijk en proactief? *(1-5 sterren)*
3. Hoe tevreden bent u over de **uiteindelijke oplossing**? *(1-5 sterren)*
4. Heeft de escalatie uw **vertrouwen** in de dienstverlening beïnvloed? *(positief/neutraal/negatief)*

**Score-gebruik:** Recovery-effectiviteit meten. Verbetering van escalatieproces. Vertrouwensherstel-tracking.

#### 11.2.3 SLA-breach feedback

**Trigger:** Na afhandeling van een ticket waarbij de SLA-deadline is overschreden (100% SLA-breach).
**Verzending:** OpenClaw stuurt via portal + email, na oplevering van het vertraagde ticket.
**Resultaten:** FlowInquiry (ticket-niveau) + SLA-dashboard.

**Vragen:**

1. Bent u **tijdig geïnformeerd** over de vertraging? *(ja/nee)*
2. Was de **uitleg** over de oorzaak van de vertraging bevredigend? *(1-5 sterren)*
3. Hoe tevreden bent u over het **eindresultaat** ondanks de vertraging? *(1-5 sterren)*
4. Heeft de vertraging **impact gehad** op uw eigen planning of processen? *(ja, significant / ja, beperkt / nee)*

**Score-gebruik:** SLA-breach impact-analyse. Verbetering van proactieve communicatie bij vertragingen. Input voor SLA-tier aanpassingen.

#### 11.2.4 Milestone-feedback

**Trigger:** Na deelopleveringen van grotere trajecten (Brown Paper Analysis, Migration Planning, Green Paper).
**Verzending:** OpenClaw stuurt via portal + email, na elke tussentijdse oplevering (bijv. na stap 3 van 7 in Brown Paper).
**Resultaten:** FlowInquiry (ticket-niveau) + projectvoortgang dashboard.

**Vragen:**

1. Hoe tevreden bent u over dit **tussenresultaat**? *(1-5 sterren)*
2. Sluit het resultaat aan bij uw **verwachtingen**? *(ja/deels/nee)*
3. Zijn er **bijsturingen** nodig voor de volgende stappen? *(open tekstveld)*
4. Hoe ervaart u de **voortgangscommunicatie** tot nu toe? *(1-5 sterren)*
5. Heeft u **aanvullende input** voor het vervolg? *(open tekstveld)*

**Score-gebruik:** Bijsturing vóór eindresultaat. Vroege signalering van ontevredenheid. Verbetering van tussentijdse communicatie.

### 11.3 Meetstructuur en rapportage

| Metric | Berekening | Frequentie | Dashboard |
|--------|-----------|------------|-----------|
| **Ticket-CSAT** | Gemiddelde van ticket-evaluatie sterren (vragen 1-3) | Per ticket | SLA-dashboard |
| **Portfolio-CSAT** | Gemiddelde van applicatie-review sterren | Per kwartaal | Kwartaalrapport |
| **NPS** | % Promoters (9-10) − % Detractors (0-6) | Per kwartaal | Management dashboard |
| **Onboarding-score** | Gemiddelde van onboarding-peiling sterren | Per nieuwe klant | Onboarding-metrics |
| **Recovery-score** | Gemiddelde van escalatie-recovery sterren | Per escalatie | Escalatie-metrics |
| **Conversie-ratio** | % Quickscans dat doorgaat naar Fase II | Per maand | Conversie-dashboard |

Alle scores worden opgenomen in het **maandrapport** (Fase V) en zijn beschikbaar via het **klantportaal** voor self-service inzage.

---

## 12. Bronnen

- [OpenClaw + FlowInquiry HQ Analyse](openclaw-flowinquiry-hq-analysis.md) — Architectuur en integratie plan
- [9-Lane Kanban Implementation](../../docs/roadmap/) — Event-driven kanban systeem
- [MarQed.ai Platform](https://marqed.ai) — Hoofdplatform
