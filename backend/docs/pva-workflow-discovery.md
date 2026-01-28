# PVA: Workflow & User Journey Discovery

**Document**: Plan van Aanpak - Workflow Inventarisatie
**Datum**: 2026-01-28
**Status**: VOORSTEL
**Prioriteit**: HOOG - Moet VOOR business logic extraction

---

## 1. Aanleiding

Tijdens de Brown Paper test bleek dat:
1. De applicatie **188 services** bevat
2. Er **50+ workflow-gerelateerde** services zijn
3. Er geen centrale documentatie is van alle workflows en user journeys
4. Aanpassingen aan één workflow kunnen impact hebben op andere workflows

**Risico**: Zonder volledig beeld kunnen we geen veilige aanpassingen maken.

---

## 2. Doelstelling

Een complete inventarisatie maken van:

1. **Alle workflows** in de applicatie
2. **User journeys** per workflow
3. **Dependencies** tussen workflows
4. **Shared services** die meerdere workflows gebruiken
5. **Data flows** tussen componenten

---

## 3. Scope

### In Scope

| Categorie | Beschrijving |
|-----------|--------------|
| Workflows | Alle geïdentificeerde workflow services |
| User Journeys | Stap-voor-stap flows van gebruiker perspectief |
| API Endpoints | Alle endpoints per workflow |
| Services | Alle services die workflows ondersteunen |
| Data Models | Database tabellen en relaties |
| Agents | AI agents die in workflows worden gebruikt |

### Geïdentificeerde Workflow Categorieën

```
1. CONFUCIUS WORKFLOWS
   ├── Brown Paper Workflow      - Legacy code analyse
   ├── Migration Workflow        - Migratie planning
   ├── Green Paper Workflow      - ? (te onderzoeken)
   └── Quality Workflow          - ? (te onderzoeken)

2. CCPM WORKFLOWS
   └── Workflow Worktree         - Git-based workflow management

3. GRAPH WORKFLOWS
   ├── graph_workflow_service
   └── graph_workflow_integration

4. KANBAN WORKFLOWS
   ├── kanban_agent_service      - AI-gestuurde kanban
   ├── lane_progression_service  - Lane management
   ├── kanban_event_service      - Event handling
   └── kanban_quality_gate       - Quality gates

5. MIGRATION WORKFLOWS
   ├── migration_analyzer        - Code analyse
   ├── migration_architecture    - Architectuur planning
   ├── migration_enhanced        - Enhanced analyse
   └── migration_planning_orch   - Orchestratie

6. PROJECT WORKFLOWS
   ├── project_wizard_service    - Project setup
   ├── project_assessment_orch   - Assessment
   └── software_intake_service   - Intake proces

7. AGENT WORKFLOWS
   ├── agent_service             - Agent management
   ├── agent_validation_loop     - Validatie
   └── agent_evolution_service   - Evolution/learning

8. EXTRACTION WORKFLOWS
   ├── deep_extraction_service   - Deep code extraction
   ├── extraction_integration    - Integration
   └── hierarchical_story_extr   - Story extraction

9. QUALITY WORKFLOWS
   ├── quality_gate_integration  - Quality gates
   ├── invest_validator_service  - INVEST validation
   └── spec_shaping_service      - Spec refinement

10. SECURITY WORKFLOWS
    └── security_workflow_service - Security checks
```

---

## 4. Deliverables

### 4.1 Workflow Catalogus

Per workflow:

```yaml
workflow:
  name: "Brown Paper Workflow"
  category: "Confucius"
  purpose: "Legacy code analyse en migratie planning"

  entry_points:
    - "POST /api/brown-paper/marqed/start"
    - "POST /api/confucius/workflows/brown-paper"

  user_journey:
    - step: 1
      action: "Start sessie"
      endpoint: "POST /marqed/start"
      input: "project_name, source_path"
      output: "session_id"

    - step: 2
      action: "Beantwoord 8 vragen"
      endpoint: "POST /marqed/{id}/answer"
      input: "answer text"
      output: "next question of status change"
    # ... etc

  services_used:
    - BrownPaperService
    - MarQedBrownPaperWorkflow
    - DependencyGraphService
    - CodeAnalysisAggregatorService
    # ... etc

  agents_used:
    - "Miguel" (migration analysis)
    - "Peter" (domain extraction)
    - "Felix" (task generation)

  database_tables:
    - marqed_sessions
    - marqed_answers
    - layered_analysis_sessions
    # ... etc

  depends_on:
    - "Deep Extraction Workflow"
    - "Hierarchical Story Extraction"

  depended_by:
    - "Migration Planning Orchestrator"
```

### 4.2 User Journey Diagrammen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY: BROWN PAPER                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Gebruiker]                                                                │
│      │                                                                       │
│      │ "Ik wil legacy code analyseren"                                      │
│      ▼                                                                       │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ START   │────▶│ VRAGEN  │────▶│ ANALYSE │────▶│ TAKEN   │              │
│  │ sessie  │     │ 1-8     │     │ Miguel  │     │ Felix   │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│      │               │               │               │                      │
│      ▼               ▼               ▼               ▼                      │
│  session_id     answers[]      complexity      epics/stories                │
│                                risk_register                                │
│                                                                              │
│      ├───────────────────────────────────────────────────────┤             │
│      │                                                       │             │
│      ▼                                                       ▼             │
│  ┌─────────┐                                           ┌─────────┐        │
│  │ENHANCED │                                           │ EXPORT  │        │
│  │ANALYSIS │                                           │ results │        │
│  └─────────┘                                           └─────────┘        │
│      │                                                                      │
│      ▼                                                                      │
│  6 phases: Code → Domain → Hierarchy → Deep → Estimation → Output          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Dependency Matrix

| Workflow | Uses | Used By |
|----------|------|---------|
| Brown Paper | DependencyGraph, CodeAnalysis, ... | Migration Planning |
| Migration | Brown Paper, Architecture, ... | Project Assessment |
| Kanban | Agent, Quality Gate, ... | - |
| ... | ... | ... |

### 4.4 Service Map

```
                    ┌─────────────────────────────────────┐
                    │           API LAYER                 │
                    │  brown_paper.py, confucius.py, ...  │
                    └──────────────────┬──────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
   │   WORKFLOW  │            │   WORKFLOW  │            │   WORKFLOW  │
   │ Brown Paper │            │  Migration  │            │   Kanban    │
   └──────┬──────┘            └──────┬──────┘            └──────┬──────┘
          │                          │                          │
          │    ┌─────────────────────┴───────────┐              │
          │    │                                 │              │
          ▼    ▼                                 ▼              ▼
   ┌─────────────────┐                  ┌─────────────────┐
   │ SHARED SERVICES │                  │ SHARED SERVICES │
   │ - DependencyGraph                  │ - Agent Service │
   │ - CodeAnalysis  │                  │ - Quality Gate  │
   │ - Extraction    │                  │ - LLM Adapter   │
   └─────────────────┘                  └─────────────────┘
```

---

## 5. Aanpak

### Fase 1: Automated Discovery (1-2 dagen)

```bash
# Script om alle workflows te inventariseren
1. Parse alle service files voor class definities
2. Extract API endpoints per router
3. Map database models naar services
4. Identificeer agent configuraties
5. Genereer initiële workflow catalogus
```

### Fase 2: Manual Analysis (2-3 dagen)

Per workflow categorie:
1. Lees service code
2. Trace user journey via endpoints
3. Documenteer dependencies
4. Identificeer shared services
5. Teken flow diagrammen

### Fase 3: Validation (1 dag)

1. Review met bestaande documentatie
2. Vergelijk met test files
3. Valideer database relaties
4. Identificeer gaps

### Fase 4: Documentation (1-2 dagen)

1. Schrijf workflow catalogus
2. Maak user journey diagrammen
3. Genereer dependency matrix
4. Publiceer service map

---

## 6. Output Structuur

```
backend/docs/
├── workflows/
│   ├── index.md                    # Overzicht alle workflows
│   ├── confucius/
│   │   ├── brown-paper.md          # Brown Paper workflow
│   │   ├── migration.md            # Migration workflow
│   │   ├── green-paper.md          # Green Paper workflow
│   │   └── quality.md              # Quality workflow
│   ├── kanban/
│   │   ├── agent.md
│   │   └── progression.md
│   ├── migration/
│   │   ├── analyzer.md
│   │   └── orchestrator.md
│   └── ...
├── user-journeys/
│   ├── legacy-analysis.md          # "Ik wil legacy code analyseren"
│   ├── migration-planning.md       # "Ik wil een migratie plannen"
│   ├── project-intake.md           # "Ik wil een nieuw project starten"
│   └── ...
├── architecture/
│   ├── service-map.md
│   ├── dependency-matrix.md
│   └── data-flow.md
└── pva-business-logic-extraction.md  # (bestaand - blocked by discovery)
```

---

## 7. Prioritering

| # | Workflow Categorie | Prioriteit | Reden |
|---|-------------------|------------|-------|
| 1 | Confucius (Brown Paper, Migration) | HOOG | Direct gerelateerd aan huidige test |
| 2 | Extraction (Deep, Hierarchical) | HOOG | Nodig voor business logic extraction |
| 3 | Kanban | MEDIUM | Belangrijke user-facing feature |
| 4 | CCPM | MEDIUM | Git workflow integration |
| 5 | Project/Intake | MEDIUM | Onboarding flow |
| 6 | Security | LAAG | Ondersteunend |
| 7 | Overige | LAAG | Inventariseer, detail later |

---

## 8. Tijdlijn

| Fase | Activiteit | Dagen | Cumulatief |
|------|------------|-------|------------|
| 1 | Automated Discovery | 1-2 | 2 |
| 2 | Manual Analysis (prioriteit 1-2) | 2-3 | 5 |
| 3 | Validation | 1 | 6 |
| 4 | Documentation | 1-2 | 8 |
| - | **Totaal Discovery** | **5-8** | - |
| 5 | Business Logic Extraction (na discovery) | 7-9 | 15-17 |

---

## 9. Success Criteria

- [ ] Alle 188 services zijn gecategoriseerd
- [ ] Top 10 workflows hebben volledige documentatie
- [ ] User journeys zijn gedocumenteerd voor hoofdflows
- [ ] Dependency matrix is compleet voor prioriteit 1-2
- [ ] Service map toont alle connecties
- [ ] Gaps en inconsistenties zijn geïdentificeerd

---

## 10. Risico's

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Te veel detail, te weinig tijd | Vertraging | Focus op prioriteit 1-2 eerst |
| Ongedocumenteerde legacy code | Incomplete analyse | Best effort + markeer gaps |
| Scope creep | Vertraging | Strikte prioritering |

---

## 11. Besluit Nodig

Voordat we starten:

1. **Akkoord op prioritering?** (Confucius/Extraction eerst)
2. **Akkoord op tijdsinvestering?** (5-8 dagen discovery)
3. **Wie reviewt de output?**

---

## 12. Relatie met Business Logic Extraction

```
┌─────────────────────────────────────────────────────────────────┐
│                        ROADMAP                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [NOW] PVA Workflow Discovery                                   │
│    │                                                             │
│    │  Output: Workflow catalogus, User journeys, Dependencies   │
│    │                                                             │
│    ▼                                                             │
│  [NEXT] PVA Business Logic Extraction                           │
│    │                                                             │
│    │  Nu MET context van alle workflows!                        │
│    │  Weten we welke services we moeten aanpassen               │
│    │  Weten we de impact op andere workflows                    │
│    │                                                             │
│    ▼                                                             │
│  [THEN] Implementatie                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Het Business Logic Extraction PVA is **BLOCKED** totdat we de discovery hebben afgerond.
