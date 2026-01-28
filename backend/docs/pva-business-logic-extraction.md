# PVA: Business Logic Extraction voor Epics/Stories

**Document**: Plan van Aanpak - Business Logic Driven Story Generation
**Datum**: 2026-01-28
**Status**: VOORSTEL
**Aanleiding**: Brown Paper test toonde dat gegenereerde epics/stories te generiek zijn

---

## 1. Probleemstelling

### Huidige Situatie

De Brown Paper workflow genereert **template-based** epics/stories:

```
EPIC-001: Phase 1: Foundation
  FEAT-001: Setup Implementation
    STORY: Setup Setup infrastructure
    STORY: Implement Setup core logic        <- Te generiek!
    STORY: Create Setup API endpoints
    ...
```

### Wat Ontbreekt

De gegenereerde items reflecteren **NIET** de daadwerkelijke business logica in de code:

| Wat we hebben | Wat we willen |
|---------------|---------------|
| "Implement Core Business Logic" | "Migreer Patiënt Registratie Module" |
| "Setup User Management" | "Herbouw Behandelplan Beheer met FHIR integratie" |
| "Create API endpoints" | "Implementeer Vecozo Declaratie API" |

### Root Cause

1. **Stap 4 (Tasks)** genereert stories op basis van de **migratie phases** uit Stap 2, niet op basis van code analyse
2. **Phase 2 (Domain Extraction)** vond slechts 1 domain - te weinig granulariteit
3. **Phase 3 (Hierarchical Extraction)** genereerde 0 epics - niet functioneel
4. Er is geen **koppeling** tussen de code analyse (3,051 modules) en de story generation

---

## 2. Gewenste User Journey

### Huidige Flow (AS-IS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BROWN PAPER WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Stap 1-2: Vragen & Analyse]                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                        │
│  │ 8 MarQed Vragen │ ──► Complexity: MEDIUM                                 │
│  │ (handmatig)     │     Risk Register                                      │
│  └─────────────────┘     Migratie Phases (4)                                │
│       │                                                                      │
│       │  ❌ Geen koppeling met code!                                        │
│       ▼                                                                      │
│  [Stap 4: Task Generation]                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                        │
│  │ Template-based  │ ──► 4 Epics (generiek)                                 │
│  │ Story Generator │     12 Features (generiek)                             │
│  │ (Felix Agent)   │     72 Stories (generiek)                              │
│  └─────────────────┘                                                        │
│       │                                                                      │
│       │  ❌ Stories zeggen niets over de business!                          │
│       ▼                                                                      │
│  [Stap 5-6: Enhanced Analysis]                                              │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                        │
│  │ Code Analysis   │ ──► 3,051 Modules gevonden                             │
│  │ (6 Phases)      │     7,936 Dependencies                                 │
│  │                 │     Business domains (1) ❌                            │
│  └─────────────────┘                                                        │
│                                                                              │
│  ⚠️ PROBLEEM: Code analyse komt NA story generation!                        │
│  ⚠️ PROBLEEM: Geen feedback loop naar stories!                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gewenste Flow (TO-BE)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VERBETERDE BROWN PAPER WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Stap 1: Sessie Start + Code Scan]                                         │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                                │
│  │ 8 MarQed Vragen │     │ Quick Code Scan │                                │
│  │ (handmatig)     │     │ (parallel)      │                                │
│  └────────┬────────┘     └────────┬────────┘                                │
│           │                       │                                          │
│           │         ┌─────────────┘                                          │
│           ▼         ▼                                                        │
│  [Stap 2: Contextuele Analyse]                                              │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Gecombineerde Analyse                   │                                │
│  │ • Antwoorden + Code Inzichten           │                                │
│  │ • Identificeer Business Domeinen        │ ──► Domeinen:                  │
│  │ • Match modules met domeinen            │     • Patiënt Beheer           │
│  │ • Detecteer core business entities      │     • Behandelplan             │
│  └─────────────────────────────────────────┘     • Declaraties              │
│       │                                          • Agenda/Planning          │
│       │                                          • Rapportages              │
│       ▼                                                                      │
│  [Stap 3: Business-Driven Story Generation]                                 │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Intelligente Story Generator            │                                │
│  │ • Epic per Business Domein              │ ──► EPIC: Patiënt Beheer       │
│  │ • Feature per Module Cluster            │       FEAT: Registratie        │
│  │ • Story per Functie/Screen              │         STORY: Migreer NAW     │
│  │ • Acceptatiecriteria uit code           │         STORY: Migreer BSN     │
│  └─────────────────────────────────────────┘         STORY: Validatie       │
│       │                                                                      │
│       ▼                                                                      │
│  [Stap 4: Deep Analysis & Refinement]                                       │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Story Enrichment                        │                                │
│  │ • Voeg technische details toe           │ ──► Stories met:               │
│  │ • Link naar source files                │     • Bron bestanden           │
│  │ • Schat complexity per story            │     • Complexity score         │
│  │ • Identificeer dependencies             │     • Dependencies             │
│  └─────────────────────────────────────────┘     • Acceptatiecriteria       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Concrete Verbeteringen

### 3.1 Verplaats Code Analyse naar Begin

**Huidige volgorde:**
```
Vragen → Analysis → Specification → Tasks → Enhanced Analysis
```

**Gewenste volgorde:**
```
Vragen + Quick Scan → Gecombineerde Analysis → Business-Driven Tasks → Deep Analysis
```

### 3.2 Verbeter Domain Extraction (Phase 2)

**Huidige output:** 1 domain (te weinig)

**Gewenste output voor FysioOne:**
```yaml
domains:
  - name: "Patiënt Beheer"
    modules: ["patient.asp", "patientgegevens.asp", "bsn_validatie.asp"]
    entities: ["Patient", "Adres", "Verzekering"]

  - name: "Behandelplan"
    modules: ["behandeling.asp", "diagnose.asp", "icpc_codes.asp"]
    entities: ["Behandeling", "Diagnose", "Verrichting"]

  - name: "Agenda & Planning"
    modules: ["agenda.asp", "afspraak.asp", "rooster.asp"]
    entities: ["Afspraak", "Therapeut", "Locatie"]

  - name: "Declaraties & Facturatie"
    modules: ["declaratie.asp", "vecozo.asp", "factuur.asp"]
    entities: ["Declaratie", "Factuur", "Tarief"]

  - name: "Rapportages"
    modules: ["rapport.asp", "statistiek.asp", "export.asp"]
    entities: ["Rapport", "KPI", "Export"]
```

### 3.3 Business-Driven Epic/Story Structuur

**Gewenste output:**

```yaml
epics:
  - id: "EPIC-001"
    title: "Patiënt Beheer Migratie"
    description: "Migratie van alle patiënt-gerelateerde functionaliteit"
    source_modules: 45
    estimated_complexity: HIGH
    features:
      - id: "FEAT-001"
        title: "Patiënt Registratie"
        source_files: ["patient.asp", "nieuw_patient.asp"]
        stories:
          - title: "Migreer NAW gegevens invoer"
            source: "patient.asp:120-180"
            acceptance_criteria:
              - "Alle velden uit legacy form zijn beschikbaar"
              - "Validatie regels zijn behouden"
              - "Postcode lookup werkt"
            story_points: 5

          - title: "Migreer BSN validatie"
            source: "bsn_validatie.asp"
            acceptance_criteria:
              - "11-proef validatie werkt"
              - "Dubbel BSN check actief"
            story_points: 3

          - title: "Implementeer Patiënt zoeken"
            source: "patient_zoek.asp"
            acceptance_criteria:
              - "Zoeken op naam, BSN, geboortedatum"
              - "Resultaten tonen NAW + laatste afspraak"
            story_points: 5

  - id: "EPIC-002"
    title: "Behandelplan Migratie"
    description: "Migratie van behandelplan en diagnose functionaliteit"
    source_modules: 32
    features:
      - id: "FEAT-003"
        title: "Diagnose Registratie"
        stories:
          - title: "Migreer ICPC code selectie"
            source: "diagnose.asp"
            acceptance_criteria:
              - "ICPC-1 codelijst doorzoekbaar"
              - "Meerdere diagnoses per patiënt"
            story_points: 5
```

---

## 4. Technische Aanpassingen

### 4.1 Nieuwe Service: BusinessDomainExtractor

```python
class BusinessDomainExtractor:
    """Extract business domains from code analysis results."""

    async def extract_domains(
        self,
        modules: List[CodeModule],
        dependencies: List[Edge],
        file_contents: Dict[str, str]
    ) -> List[BusinessDomain]:
        """
        1. Cluster modules op basis van dependencies
        2. Analyseer file/function names voor domain hints
        3. Extract entities uit code (classes, tables, forms)
        4. Match met common healthcare/physio domains
        5. Return gestructureerde domains
        """
```

### 4.2 Verbeterde Story Generator

```python
class BusinessDrivenStoryGenerator:
    """Generate stories based on actual code structure."""

    async def generate_stories(
        self,
        domains: List[BusinessDomain],
        code_analysis: Phase1Result,
        migration_context: MigrationAnalysisResult
    ) -> TaskHierarchy:
        """
        1. Epic per business domain
        2. Feature per module cluster
        3. Story per:
           - Screen/form in legacy code
           - API endpoint
           - Business rule/validation
           - Data entity CRUD
        4. Enriched met source references
        """
```

### 4.3 Aanpassing Workflow Volgorde

```python
# brown_paper_service.py

async def run_marqed_workflow(self, session_id: str):
    # Stap 1: Start + Quick Code Scan (parallel)
    answers = await self.collect_answers(session_id)
    quick_scan = await self.quick_code_scan(session.project_path)

    # Stap 2: Gecombineerde Analysis
    analysis = await self.analyze_with_code_context(
        answers=answers,
        code_scan=quick_scan
    )

    # Stap 3: Business-Driven Tasks (NIEUW)
    domains = await self.extract_business_domains(quick_scan)
    tasks = await self.generate_business_driven_tasks(
        domains=domains,
        analysis=analysis
    )

    # Stap 4: Deep Analysis & Enrichment
    enhanced = await self.run_enhanced_analysis(session_id)
    enriched_tasks = await self.enrich_tasks_with_analysis(
        tasks=tasks,
        enhanced=enhanced
    )
```

---

## 5. Voorbeeld Output: FysioOne-Classic

### Verwachte Epics na Verbetering

| Epic | Titel | Modules | Stories |
|------|-------|---------|---------|
| EPIC-001 | Patiënt Beheer Migratie | 45 | 18 |
| EPIC-002 | Behandelplan & Diagnose | 32 | 14 |
| EPIC-003 | Agenda & Planning | 28 | 12 |
| EPIC-004 | Declaraties & Vecozo | 25 | 15 |
| EPIC-005 | Rapportages & Statistiek | 18 | 8 |
| EPIC-006 | Gebruikersbeheer & Rechten | 15 | 10 |
| EPIC-007 | Systeem & Configuratie | 20 | 8 |
| EPIC-008 | Data Migratie & Cutover | - | 12 |

### Voorbeeld Stories voor EPIC-001

```markdown
## EPIC-001: Patiënt Beheer Migratie

### FEAT-001: Patiënt Registratie
- [ ] STORY-001: Migreer patiënt aanmaken form (patient_nieuw.asp) [5 SP]
- [ ] STORY-002: Migreer patiënt wijzigen form (patient_edit.asp) [3 SP]
- [ ] STORY-003: Implementeer BSN validatie (11-proef) [2 SP]
- [ ] STORY-004: Migreer postcode/adres lookup [3 SP]
- [ ] STORY-005: Implementeer duplicate check [3 SP]

### FEAT-002: Patiënt Zoeken
- [ ] STORY-006: Migreer zoekscherm (patient_zoek.asp) [5 SP]
- [ ] STORY-007: Implementeer filters (naam, BSN, datum) [3 SP]
- [ ] STORY-008: Migreer zoekresultaten weergave [3 SP]

### FEAT-003: Patiënt Dossier
- [ ] STORY-009: Migreer dossier overzicht (patient_dossier.asp) [8 SP]
- [ ] STORY-010: Migreer historie weergave [5 SP]
- [ ] STORY-011: Implementeer documenten upload [5 SP]
```

---

## 6. Acceptatiecriteria voor dit PVA

- [ ] Domain extraction vindt minimaal 5 business domeinen voor FysioOne
- [ ] Elke epic is gekoppeld aan concrete source modules
- [ ] Stories bevatten references naar source files
- [ ] Acceptatiecriteria zijn afgeleid uit de legacy code
- [ ] Story points zijn gebaseerd op code complexity

---

## 7. Geschatte Inspanning

| Component | Inspanning |
|-----------|------------|
| BusinessDomainExtractor service | 2-3 dagen |
| BusinessDrivenStoryGenerator | 2-3 dagen |
| Workflow volgorde aanpassen | 1 dag |
| Integratie & testen | 2 dagen |
| **Totaal** | **7-9 dagen** |

---

## 8. Conclusie

De huidige Brown Paper workflow is functioneel voor **migratie planning op hoog niveau**, maar mist de koppeling met de **daadwerkelijke business logica** in de code.

Door de code analyse naar voren te halen en een business-driven story generator te implementeren, kunnen we:

1. **Relevantere epics** - Gebaseerd op echte business domeinen
2. **Specifiekere stories** - Met source references en acceptatiecriteria
3. **Betere schattingen** - Gebaseerd op code complexity
4. **Traceerbaarheid** - Van story naar legacy code naar nieuwe implementatie
