# Confucius Workflows - Complete Documentation

**Datum**: 2026-01-28
**Status**: ACTIEF
**Versie**: 1.0

---

## 1. Overzicht

De Confucius module bevat 4 gespecialiseerde workflow orchestrators die elk een specifiek doel dienen:

| Workflow | Doel | Stages | Primaire Agents |
|----------|------|--------|-----------------|
| **Brown Paper** | Legacy code analyse & migratie planning | 6 | Miguel, Peter, Betty, Vicky, Felix, Quinn, Diana |
| **Migration** | Migratie specificatie & planning | 7 | Miguel, Quinn, Vicky, Peter, Betty, Felix, Paul |
| **Green Paper** | Greenfield project planning | 7 | Peter, Betty, Vicky, Felix, Quinn, Paul, Eliza |
| **Quality** | Code kwaliteit analyse & remediatie | 5 | Miguel, Quinn, Marcus, Tessa |

---

## 2. Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFUCIUS ORCHESTRATION LAYER                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  WorkflowStage │  │WorkflowContext │  │ WorkflowResult │    │
│  │   (dataclass)  │  │   (runtime)    │  │   (output)     │    │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘    │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              ▼                                   │
│                 ┌────────────────────────┐                      │
│                 │  WorkflowOrchestrator  │ ◄─── Base Class      │
│                 │  (abstract)            │                      │
│                 └───────────┬────────────┘                      │
│                             │                                    │
│      ┌──────────────────────┼──────────────────────┐            │
│      ▼                      ▼                      ▼            │
│ ┌──────────┐         ┌──────────┐         ┌──────────┐         │
│ │ Brown    │         │Migration │         │ Green    │         │
│ │ Paper    │         │Orchestr. │         │ Paper    │         │
│ └────┬─────┘         └────┬─────┘         └────┬─────┘         │
│      │                    │                    │                │
│      │               ┌────┴────┐               │                │
│      │               ▼         │               │                │
│      │         ┌──────────┐    │               │                │
│      │         │ Quality  │    │               │                │
│      │         │Orchestr. │    │               │                │
│      │         └────┬─────┘    │               │                │
│      │              │          │               │                │
│      └──────────────┼──────────┼───────────────┘                │
│                     ▼          ▼                                 │
│            ┌──────────────────────────┐                         │
│            │    Quality Gate System   │                         │
│            │  (Quinn + INVEST Validator)                        │
│            └──────────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. WorkflowStage Specificatie

Elke stage in een workflow heeft de volgende eigenschappen:

```python
@dataclass
class WorkflowStage:
    name: str                    # Unieke stage naam
    description: str             # Beschrijving van de stage
    agents: List[str]            # Agents die deze stage uitvoeren
    required: bool = True        # Is de stage verplicht?
    depends_on: List[str] = []   # Dependencies op andere stages
    parallel_agents: bool = False # Kunnen agents parallel draaien?
    quality_threshold: float = 0.85  # Minimum kwaliteitsscore
    timeout_minutes: int = 30    # Maximum uitvoeringstijd
```

---

## 4. Workflow Details

### 4.1 Brown Paper Workflow

**Doel**: Analyse van legacy code voor migratie planning

**Entry Points**:
- `POST /api/brown-paper/marqed/start`
- `POST /api/confucius/workflows/brown-paper`

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWN PAPER WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [INPUT] project_path, tech_stack, answers (8 MarQed vragen)    │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 1: CODE_UNDERSTANDING                                  ││
│  │ Agents: Miguel                                               ││
│  │ Output: dependency_graph, code_analysis, layered_analysis    ││
│  │ Quality: 0.85 (metrics domain)                               ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 2: DOMAIN_EXTRACTION                                   ││
│  │ Agents: Peter, Betty                                         ││
│  │ Depends: code_understanding                                  ││
│  │ Output: domains, business_capabilities, domain_boundaries    ││
│  │ Quality: 0.80 (requirements domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 3: USER_JOURNEY_EXTRACTION                             ││
│  │ Agents: Vicky                                                ││
│  │ Depends: domain_extraction                                   ││
│  │ Output: user_journeys, personas, workflows                   ││
│  │ Quality: 0.85 (ux domain)                                    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 4: STORY_EXTRACTION                                    ││
│  │ Agents: Felix, Quinn                                         ││
│  │ Depends: user_journey_extraction                             ││
│  │ Output: epics, features, stories (initial)                   ││
│  │ Quality: 0.85 (architecture domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 5: DEEP_EXTRACTION                                     ││
│  │ Agents: Marcus, Betty (parallel)                             ││
│  │ Depends: story_extraction                                    ││
│  │ Output: refined stories, conflicts, consensus_confidence     ││
│  │ Quality: 0.90 (council validation)                           ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 6: ESTIMATION                                          ││
│  │ Agents: Eliza                                                ││
│  │ Depends: deep_extraction                                     ││
│  │ Output: story_points, function_points, effort_hours          ││
│  │ Quality: 0.85 (estimation domain)                            ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 7: OUTPUT_CONSOLIDATION                                ││
│  │ Agents: Diana                                                ││
│  │ Depends: estimation                                          ││
│  │ Output: final_report, recommendations, next_steps            ││
│  │ Quality: 0.85 (documentation domain)                         ││
│  └─────────────────────────────────────────────────────────────┘│
│     │                                                            │
│     ▼                                                            │
│  [OUTPUT] EnhancedAnalysisResponse with all phase results       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Services Used**:
- `BrownPaperService` (main orchestration)
- `MarQedBrownPaperWorkflow` (interview flow)
- `DependencyGraphService`
- `CodeAnalysisAggregatorService`
- `LayeredAnalysisService`
- `HierarchicalStoryExtractionService`
- `DeepExtractionService`
- `BrownPaperEstimationService`
- `LLMCouncilService`

---

### 4.2 Migration Workflow

**Doel**: Migratie specificatie en planning van legacy naar modern

**Entry Points**:
- `POST /api/confucius/workflows/migration`
- `POST /api/migration/analyze`

```
┌─────────────────────────────────────────────────────────────────┐
│                    MIGRATION WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [INPUT] answers (8 vragen), source_path, target_tech           │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 1: VALIDATE_ANSWERS                                    ││
│  │ Agents: - (validation only)                                  ││
│  │ Output: validated_answers, answers_count                     ││
│  │ Required: 8/8 answers for proceeding                         ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 2: TECHNICAL_ANALYSIS                                  ││
│  │ Agents: Miguel                                               ││
│  │ Depends: validate_answers                                    ││
│  │ Output: tech_stack_detected, complexity_score, legacy_findings││
│  │ Quality: 0.85 (metrics domain)                               ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 3: SECURITY_ANALYSIS (Fase 37)                         ││
│  │ Agents: Quinn                                                ││
│  │ Depends: technical_analysis                                  ││
│  │ Output: security_findings, cwe_top_25_coverage, scanners_used││
│  │ Quality: 0.90 (security domain)                              ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 4: GENERATE_SPECIFICATION                              ││
│  │ Agents: Peter, Betty                                         ││
│  │ Depends: security_analysis                                   ││
│  │ Output: specification (migration_context, architecture)      ││
│  │ Quality: 0.85 (requirements domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 5: GENERATE_TASKS                                      ││
│  │ Agents: Felix                                                ││
│  │ Depends: generate_specification                              ││
│  │ Output: epics, features, stories, migration_waves            ││
│  │ Quality: 0.85 (architecture domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 6: ESTIMATE_EFFORT                                     ││
│  │ Agents: Paul, Eliza                                          ││
│  │ Depends: generate_tasks                                      ││
│  │ Output: effort_by_wave, total_effort_hours, function_points  ││
│  │ Quality: 0.85 (estimation domain)                            ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 7: QUALITY_REVIEW                                      ││
│  │ Agents: Quinn                                                ││
│  │ Depends: estimate_effort                                     ││
│  │ Output: quality_score, recommendations, approval_status      ││
│  │ Quality: 0.90 (quality gate)                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│     │                                                            │
│     ▼                                                            │
│  [OUTPUT] MigrationAnalysisResponse                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**8 Migration Questions**:
1. `q1_legacy_system` - Beschrijving legacy systeem
2. `q2_target_platform` - Doel platform
3. `q3_data_migration` - Data migratie requirements
4. `q4_integrations` - Externe integraties
5. `q5_users` - Gebruikers en rollen
6. `q6_constraints` - Technische constraints
7. `q7_risks` - Bekende risico's
8. `q8_timeline` - Gewenste tijdlijn

---

### 4.3 Green Paper Workflow

**Doel**: Greenfield project planning en specificatie

**Entry Points**:
- `POST /api/green-paper/sessions`
- `POST /api/confucius/workflows/green-paper`

```
┌─────────────────────────────────────────────────────────────────┐
│                    GREEN PAPER WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [INPUT] project_name, answers (6 vragen)                       │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 1: VALIDATE_VISION                                     ││
│  │ Agents: - (validation only)                                  ││
│  │ Output: validated_vision, project_name confirmed             ││
│  │ Required: project_name + vision answer                       ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 2: REQUIREMENTS_CONSTITUTION                           ││
│  │ Agents: Peter, Betty                                         ││
│  │ Depends: validate_vision                                     ││
│  │ Output: constitution (requirements, stakeholders, criteria)  ││
│  │ Quality: 0.85 (requirements domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 3: UX_DESIGN                                           ││
│  │ Agents: Vicky                                                ││
│  │ Depends: requirements_constitution                           ││
│  │ Output: personas, user_flows, wireframes, design_tokens      ││
│  │ Quality: 0.85 (ux domain)                                    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 4: ARCHITECTURE_DESIGN                                 ││
│  │ Agents: Felix                                                ││
│  │ Depends: ux_design                                           ││
│  │ Output: architecture, component_diagram, api_design, data_model│
│  │ Quality: 0.90 (architecture domain)                          ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 5: SECURITY_REQUIREMENTS (Fase 37)                     ││
│  │ Agents: Quinn                                                ││
│  │ Depends: architecture_design                                 ││
│  │ Output: security_requirements (auth, data_protection, etc.)  ││
│  │ Quality: 0.90 (security domain)                              ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 6: IMPLEMENTATION_PLANNING                             ││
│  │ Agents: Paul, Eliza                                          ││
│  │ Depends: security_requirements                               ││
│  │ Output: milestones, sprints, roadmap, effort_estimate        ││
│  │ Quality: 0.85 (planning domain)                              ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 7: QUALITY_REVIEW                                      ││
│  │ Agents: Quinn                                                ││
│  │ Depends: implementation_planning                             ││
│  │ Output: quality_score, completeness_check, passes_gate       ││
│  │ Quality: 0.90 (quality gate)                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│     │                                                            │
│     ▼                                                            │
│  [OUTPUT] GreenPaperResponse with full specification            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**6 Green Paper Questions**:
1. `vision` - Project visie en doel
2. `users` - Doelgroepen en stakeholders
3. `features` - Core functionaliteiten
4. `constraints` - Technische en business constraints
5. `success` - Success criteria
6. `timeline` - Gewenste tijdlijn

---

### 4.4 Quality Workflow

**Doel**: Code kwaliteitsanalyse en remediatie planning

**Entry Points**:
- `POST /api/quality/scan`
- `POST /api/confucius/workflows/quality`

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [INPUT] project_path, tech_stack, scanners[]                   │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 1: SCAN_EXECUTION                                      ││
│  │ Agents: Miguel                                               ││
│  │ Output: scan_results, files_scanned, issues_found            ││
│  │ Quality: 0.85 (metrics domain)                               ││
│  │ Required: Yes                                                ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 2: METRICS_ANALYSIS                                    ││
│  │ Agents: Miguel                                               ││
│  │ Depends: scan_execution                                      ││
│  │ Output: metrics_summary, complexity_breakdown, trends        ││
│  │ Quality: 0.85 (metrics domain)                               ││
│  │ Required: Yes                                                ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 3: QUALITY_REVIEW                                      ││
│  │ Agents: Quinn                                                ││
│  │ Depends: metrics_analysis                                    ││
│  │ Output: quality_score, critical_issues, gate_status          ││
│  │ Quality: 0.90 (quality gate)                                 ││
│  │ Required: Yes                                                ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 4: REMEDIATION_PLANNING                                ││
│  │ Agents: Marcus                                               ││
│  │ Depends: quality_review                                      ││
│  │ Output: remediation_plan, quick_wins, priority_order         ││
│  │ Quality: 0.85 (planning domain)                              ││
│  │ Required: No (conditional on findings)                       ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ STAGE 5: TEST_VALIDATION                                     ││
│  │ Agents: Tessa                                                ││
│  │ Depends: remediation_planning                                ││
│  │ Output: tests_generated, tests_passed, validation_status     ││
│  │ Quality: 0.85 (testing domain)                               ││
│  │ Required: No (conditional on remediation)                    ││
│  └─────────────────────────────────────────────────────────────┘│
│     │                                                            │
│     ▼                                                            │
│  [OUTPUT] QualityAnalysisResponse                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Agent Mapping

| Agent | Rol | Workflows | Domain |
|-------|-----|-----------|--------|
| **Miguel** | Code Analysis | BP, Mig, Qual | metrics |
| **Peter** | Product Owner | BP, Mig, GP | requirements |
| **Betty** | Business Analyst | BP, Mig, GP | requirements |
| **Vicky** | UX Designer | BP, GP | ux |
| **Felix** | Architect | BP, Mig, GP | architecture |
| **Quinn** | Quality Guard | BP, Mig, GP, Qual | security/quality |
| **Paul** | Project Lead | Mig, GP | planning |
| **Eliza** | Estimator | BP, GP | estimation |
| **Diana** | Documentation | BP | documentation |
| **Marcus** | Code Refactoring | BP, Qual | refactoring |
| **Tessa** | Testing | Qual | testing |

---

## 6. Test Coverage

### 6.1 Bestaande Unit Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/unit/confucius/workflows/test_workflow_orchestrators.py` | Alle 4 orchestrators | ✅ ACTIEF |
| `tests/unit/confucius/quality/test_quality_gates.py` | Quality gates | ✅ ACTIEF |

**Gedekte Functionaliteit**:
- [x] WorkflowStage creation en serialization
- [x] WorkflowContext state management
- [x] WorkflowResult success/failure
- [x] BrownPaperOrchestrator stages (6)
- [x] MigrationOrchestrator stages (7) + questions (8)
- [x] GreenPaperOrchestrator stages (7) + questions (6)
- [x] QualityOrchestrator stages (5)
- [x] Stage dependencies checking
- [x] Domain detection for quality gates
- [x] Validation with missing answers

### 6.2 Bestaande Integration Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/integration/workflows/test_brown_paper_enhanced.py` | Enhanced analysis | ✅ ACTIEF |
| `tests/unit/workflows/test_green_paper_workflow.py` | Green Paper E2E | ⚠️ TODO stubs |
| `tests/integration/workflows/test_restartable_workflows.py` | Restart/recovery | ✅ ACTIEF |

### 6.3 Test Gaps (Te Implementeren)

#### Unit Tests Nodig:

| Test | Prioriteit | Reden |
|------|------------|-------|
| `test_brown_paper_stage_execution.py` | HOOG | Individuele stage executie |
| `test_migration_stage_execution.py` | HOOG | Individuele stage executie |
| `test_agent_handoff.py` | MEDIUM | Agent-to-agent data transfer |
| `test_quality_threshold_enforcement.py` | MEDIUM | Threshold validation |

#### Integration Tests Nodig:

| Test | Prioriteit | Reden |
|------|------------|-------|
| `test_brown_paper_full_workflow.py` | HOOG | Complete workflow E2E |
| `test_migration_full_workflow.py` | HOOG | Complete workflow E2E |
| `test_green_paper_full_workflow.py` | MEDIUM | Complete workflow E2E |
| `test_quality_full_workflow.py` | MEDIUM | Complete workflow E2E |
| `test_workflow_error_recovery.py` | HOOG | Error handling en recovery |
| `test_workflow_concurrent_sessions.py` | MEDIUM | Concurrent session handling |

---

## 7. Quality Gates Integration

Elke stage wordt gevalideerd door het Quality Gate systeem:

```python
DOMAIN_THRESHOLDS = {
    "metrics": 0.85,        # Miguel's output
    "requirements": 0.80,   # Peter/Betty's output
    "architecture": 0.85,   # Felix's output
    "security": 0.90,       # Quinn's output
    "ux": 0.85,            # Vicky's output
    "estimation": 0.85,     # Eliza's output
    "documentation": 0.85,  # Diana's output
    "testing": 0.85,       # Tessa's output
}
```

---

## 8. Error Handling

### Stage Failure Recovery

```
Stage fails → Retry (max 3) → Peer assistance → Human escalation
```

### Workflow Checkpoints

- Workflows zijn restartable vanaf elke stage
- Context wordt opgeslagen na elke succesvolle stage
- Failed workflows kunnen worden hervat met `resume_from` parameter

---

## 9. API Endpoints

### Brown Paper

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brown-paper/marqed/start` | Start MarQed sessie |
| POST | `/api/brown-paper/marqed/{id}/answer` | Beantwoord vraag |
| GET | `/api/brown-paper/marqed/{id}/status` | Haal status op |
| POST | `/api/brown-paper/marqed/{id}/enhanced` | Start enhanced analysis |

### Migration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/migration/analyze` | Start migratie analyse |
| GET | `/api/migration/{id}/status` | Haal status op |
| POST | `/api/migration/{id}/specification` | Genereer specificatie |

### Green Paper

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/green-paper/sessions` | Start sessie |
| POST | `/api/green-paper/sessions/{id}/answers` | Submit antwoorden |
| POST | `/api/green-paper/sessions/{id}/constitution` | Genereer constitution |
| POST | `/api/green-paper/sessions/{id}/specification` | Genereer specificatie |

### Quality

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/quality/scan` | Start kwaliteitsscan |
| GET | `/api/quality/{id}/metrics` | Haal metrics op |
| POST | `/api/quality/{id}/remediate` | Start remediatie |

---

## 10. Dependencies

### Shared Services

```
Confucius Workflows
       │
       ├── DependencyGraphService (all workflows)
       ├── CodeAnalysisAggregatorService (BP, Mig, Qual)
       ├── AgentService (all workflows)
       ├── LLMCouncilService (BP deep extraction)
       ├── QualityGateService (all workflows)
       ├── INVESTValidatorService (task validation)
       └── HierarchicalStoryExtractionService (BP, Mig)
```

### Database Tables

| Table | Workflow | Purpose |
|-------|----------|---------|
| `marqed_sessions` | BP | MarQed session state |
| `marqed_answers` | BP | Question answers |
| `migration_sessions` | Mig | Migration session state |
| `green_paper_sessions` | GP | Green paper state |
| `quality_scans` | Qual | Scan results |
| `workflow_contexts` | All | Stage results |

---

## 11. Volgende Stappen

### Taak #6: Unit Tests Confucius Services

- [ ] `test_brown_paper_stage_execution.py`
- [ ] `test_migration_stage_execution.py`
- [ ] `test_green_paper_stage_execution.py`
- [ ] `test_quality_stage_execution.py`
- [ ] `test_agent_handoff.py`

### Taak #7: Integration Tests Confucius Workflows

- [ ] `test_brown_paper_full_workflow.py`
- [ ] `test_migration_full_workflow.py`
- [ ] `test_green_paper_full_workflow.py`
- [ ] `test_quality_full_workflow.py`
- [ ] `test_workflow_error_recovery.py`

---

## 12. Changelog

| Datum | Versie | Wijziging |
|-------|--------|-----------|
| 2026-01-28 | 1.0 | Initiële documentatie |
