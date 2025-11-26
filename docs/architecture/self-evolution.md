# Self-Evolution Layer Architecture

**Status:** Week 17-26 (Planned)
**Bron:** github.com/zeeneddie/AgentEvolver
**Impact:** Transformeert agents van statisch naar zelf-verbeterend

---

## Design Filosofie

**"Learn, Adapt, Evolve"** - Agents verbeteren zichzelf continu op basis van:
1. Ervaring uit eerdere taken
2. Analyse van successen en failures
3. Zelf-gegenereerde trainingstaken

---

## High-Level Architectuur

```
+---------------------------------------------------------------------+
|                     SELF-EVOLUTION SYSTEM                            |
|                                                                      |
|  +------------------+   +------------------+   +----------------+    |
|  | SELF-QUESTIONING |   | SELF-NAVIGATING  |   | SELF-          |    |
|  |                  |   |                  |   | ATTRIBUTING    |    |
|  | - Task Generator |   | - Experience     |   | - Outcome      |    |
|  | - Environment    |   |   Consultant     |   |   Tracker      |    |
|  |   Explorer       |   | - Pattern        |   | - Attribution  |    |
|  | - Training       |   |   Matcher        |   |   Processor    |    |
|  |   Pipeline       |   | - Relevance      |   | - Credit       |    |
|  |                  |   |   Scorer         |   |   Assigner     |    |
|  +--------+---------+   +--------+---------+   +-------+--------+    |
|           |                      |                     |             |
|           +----------------------+---------------------+             |
|                                  |                                   |
|  +---------------------------------------------------------------+  |
|  |                    EXPERIENCE STORE                            |  |
|  |  ChromaDB Collections:                                         |  |
|  |  - agent_experiences    (cross-task learnings)                 |  |
|  |  - successful_patterns  (wat werkte goed?)                     |  |
|  |  - failure_analysis     (wat ging fout en waarom?)             |  |
|  |  - estimation_accuracy  (schatting vs werkelijk)               |  |
|  |  - quality_metrics      (code quality over tijd)               |  |
|  +---------------------------------------------------------------+  |
|                                  |                                   |
|  +---------------------------------------------------------------+  |
|  |                    POLICY EVOLVER                              |  |
|  |  - A/B Testing Framework     - Safety Guardrails               |  |
|  |  - Gradual Rollout          - Automatic Rollback               |  |
|  |  - Performance Monitoring   - Evolution Dashboard              |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## Kern Modules

### 1. Self-Questioning Module (Automatische Taak Generatie)

**Doel:** Agent genereert zelf trainingstaken door omgeving te verkennen

```typescript
interface SelfQuestioningModule {
  // Genereer trainingstaken gebaseerd op gaps in kennis
  generateTrainingTasks(agent: Agent): Promise<TrainingTask[]>;

  // Verken environment voor edge cases
  exploreEnvironment(context: WorkflowContext): Promise<EdgeCase[]>;

  // Training pipeline voor zelf-verbetering
  runTrainingPipeline(tasks: TrainingTask[]): Promise<TrainingResult>;
}
```

**Voorbeelden per Agent:**

| Agent | Self-Questioning Voorbeeld |
|-------|---------------------------|
| Felix | Genereert edge-case specificaties |
| Quinn | Creert security test scenarios |
| Betty | Simuleert nieuwe bug types |
| Eliza | Test schattingen op historische data |

### 2. Self-Navigating Module (Ervaring-Geleide Exploratie)

**Doel:** Hergebruik van cross-task kennis voor betere beslissingen

```typescript
interface SelfNavigatingModule {
  // Raadpleeg ervaring voor huidige context
  consultExperience(context: TaskContext): Promise<ExperienceGuidance>;

  // Pattern matching tegen historische successen
  matchPatterns(input: WorkflowInput): Promise<PatternMatch[]>;

  // Bereken relevantie score
  scoreRelevance(experience: Experience, context: Context): number;
}
```

**Experience Consultation Flow:**
```
Nieuwe Taak -> Query Experience Store -> Rank by Relevance ->
-> Extract Guidance -> Apply to Current Task -> Log Outcome
```

### 3. Self-Attributing Module (Credit Assignment)

**Doel:** Identificeer welke stappen tot succes/falen leidden

```typescript
interface SelfAttributingModule {
  // Track workflow outcome
  trackOutcome(workflow: WorkflowExecution): Promise<OutcomeRecord>;

  // Analyseer causale bijdrage van elke stap
  analyzeAttribution(outcome: OutcomeRecord): Promise<Attribution>;

  // Wijs credit toe aan specifieke acties
  assignCredit(attribution: Attribution): Promise<CreditAssignment>;
}
```

**Attribution Metrics:**

| Metric | Beschrijving |
|--------|-------------|
| Success Contribution | Welke stappen droegen bij aan succes? |
| Failure Root Cause | Waar ging het mis? |
| Estimation Delta | Verschil tussen schatting en werkelijk |
| Quality Impact | Effect op code quality |

---

## 5-Stage Training Pipeline (Week 23-24)

```
DATA_COLLECTION -> SELF_QUESTIONING -> TASK_GENERATION -> TRAINING_EXECUTION -> EVALUATION
```

### Question Categories

| Category | Beschrijving | Voorbeeld |
|----------|-------------|-----------|
| `performance_gap` | Waar presteer ik onder? | "Waarom mis ik edge cases?" |
| `edge_case` | Welke edge cases mis ik? | "Welke inputs breken dit?" |
| `knowledge_gap` | Wat weet ik niet? | "Hoe werkt X bij microservices?" |
| `skill_improvement` | Hoe kan ik beter? | "Welke patterns verbeteren dit?" |
| `pattern_discovery` | Welke patterns werken? | "Wat werkte bij vergelijkbaar?" |

### Training Modes

| Mode | Questions | Tasks | Gebruik |
|------|-----------|-------|---------|
| Balanced | 5-10 | 3-5 | Steady improvement |
| Intensive | 10-20 | 8-15 | Rapid skill building |
| Focused | 2-5 | 1-3 | Targeted gap closure |

---

## Data Model

### Experience Record

```python
class ExperienceRecord(BaseModel):
    id: UUID
    agent_id: str                    # Felix, Quinn, etc.
    workflow_type: WorkType          # NEW_FEATURE, MAINTENANCE, etc.
    task_context: Dict[str, Any]     # Input parameters
    actions_taken: List[Action]      # Stappen uitgevoerd
    outcome: Outcome                 # SUCCESS, PARTIAL, FAILURE
    outcome_metrics: Dict[str, float] # Quality scores, time, etc.
    attribution: Attribution         # Credit assignment
    embedding: List[float]           # Voor semantic search
    created_at: datetime
    project_id: Optional[UUID]       # Link naar project
```

### Pattern Record

```python
class PatternRecord(BaseModel):
    id: UUID
    pattern_type: str                # "architecture", "refactoring", etc.
    pattern_name: str                # Human-readable naam
    context_requirements: Dict       # Wanneer toepasbaar?
    success_rate: float              # Historische success rate
    usage_count: int                 # Hoe vaak gebruikt?
    agents_successful: List[str]     # Welke agents gebruikten dit?
    embedding: List[float]           # Voor semantic search
```

---

## Autonomie Levels

| Level | Beschrijving | Guard Rails |
|-------|--------------|-------------|
| **Conservatief** | Alleen menselijk-goedgekeurde verbeteringen | Human approval voor elke wijziging |
| **Balanced** | Automatisch binnen guardrails | Automatic binnen thresholds, human voor grote wijzigingen |
| **Agressief** | Volledig autonoom leren | Minimal oversight, alleen alerts bij anomalieen |

**Gekozen: Balanced Mode**

---

## Safety Guardrails

```typescript
const SAFETY_GUARDRAILS = {
  // Maximale afwijking van baseline performance
  maxPerformanceDelta: 0.15,  // +/-15%

  // Minimum confidence voor automatische toepassing
  minConfidenceThreshold: 0.8,

  // Rollback trigger
  rollbackThreshold: {
    successRateDropPercent: 10,
    qualityScoreDropPercent: 15,
    estimationErrorIncreasePercent: 20,
  },

  // Human approval vereist voor:
  requireHumanApproval: [
    'policy_changes',        // Wijzigingen in agent gedrag
    'new_patterns',          // Nieuwe patterns toevoegen
    'cross_workflow_rules',  // Regels die meerdere workflows raken
  ],

  // Automatic allowed voor:
  automaticAllowed: [
    'experience_logging',    // Loggen van ervaringen
    'pattern_matching',      // Raadplegen van patterns
    'outcome_tracking',      // Bijhouden van resultaten
    'minor_weight_updates',  // Kleine gewichtsaanpassingen
  ],
};
```

---

## Integration met Bestaande Agents

**Alle 10 agents krijgen evolution capabilities:**

```typescript
interface EvolvingAgent extends Agent {
  // Bestaande capabilities
  name: string;
  role: string;
  llm: OllamaModel;

  // NIEUW: Evolution capabilities
  evolution: {
    // Raadpleeg ervaring voor beslissingen
    consultExperience(context: TaskContext): Promise<Guidance>;

    // Log outcome na taak completion
    logOutcome(result: TaskResult): Promise<void>;

    // Ontvang feedback voor verbetering
    receiveFeedback(attribution: Attribution): Promise<void>;

    // Performance metrics
    getPerformanceMetrics(): PerformanceMetrics;
  };
}
```

---

## API Endpoints

| Endpoint | Method | Beschrijving |
|----------|--------|-------------|
| `/api/evolution/experience` | POST | Log nieuwe ervaring |
| `/api/evolution/experience/search` | POST | Zoek relevante ervaringen |
| `/api/evolution/patterns` | GET | Lijst succesvolle patterns |
| `/api/evolution/attribution` | POST | Log outcome attribution |
| `/api/evolution/metrics` | GET | Evolution metrics dashboard |
| `/api/evolution/health` | GET | System health check |
| `/api/self-questioning/sessions` | GET | List sessions |
| `/api/self-questioning/sessions` | POST | Start session |
| `/api/self-questioning/sessions/{id}` | GET | Session details |
| `/api/self-questioning/metrics` | GET | All agent metrics |
| `/api/self-questioning/metrics/{agent}` | GET | Agent metrics |
| `/api/self-questioning/questions/{agent}` | GET | Agent questions |

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Agent Success Rate | Huidige rate | +15% | Before/after comparison |
| Estimation Accuracy | Huidige accuracy | +20% | Predicted vs actual hours |
| Code Quality Score | Huidige score | +10% | Quality gate scores |
| Experience Relevance | N/A | >80% | Semantic similarity score |
| Self-generated Tasks | 0 | >100/week | Task generation count |

---

## Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `agents/lib/selfQuestioningEngine.ts` | Core engine | ~800 |
| `agents/workflows/selfTrainingWorkflow.ts` | Training pipeline | ~500 |
| `app/api/self_questioning.py` | Python API | ~500 |
| `frontend/self-improvement-dashboard.html` | Dashboard UI | ~750 |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Continuous Evolution](./continuous-evolution.md) - Trend analysis and rollout
- [A/B Testing Framework](./ab-testing.md) - Experimentation framework
