# CiRA Causality Detection Architecture

**Week 123** | Based on arXiv:2101.10766 (REFSQ 2021)
**Repository**: github.com/fischJan/CiRA

---

## Overview

CiRA (Causality in Requirements Artifacts) provides BERT-based causality detection for requirements analysis. The system identifies causal relations between requirements, stories, and acceptance criteria to:

1. **Build Dependency Graphs** - Understand which stories must be completed before others
2. **Generate Test Cases** - Create positive/negative tests from cause-effect pairs
3. **Support Sprint Planning** - Topological ordering for dependency-aware sprint assignment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CiRA CAUSALITY DETECTION                             │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐       │
│  │ INPUT SOURCES   │    │   CLASSIFICATION  │    │  RELATION         │       │
│  │                 │───▶│                  │───▶│  EXTRACTION       │       │
│  │ • Requirements  │    │ • BERT Classifier│    │                   │       │
│  │ • Stories       │    │ • Rule-based     │    │ • 14 Patterns     │       │
│  │ • Acceptance    │    │ • 45 Markers     │    │ • CAUSES          │       │
│  │   Criteria      │    │ • 82% F1 Score   │    │ • ENABLES         │       │
│  │ • Features      │    │                  │    │ • BLOCKS          │       │
│  │ • Epics         │    │                  │    │ • DEPENDS_ON      │       │
│  └─────────────────┘    └──────────────────┘    └─────────┬─────────┘       │
│                                                           │                  │
│  ┌─────────────────────────────────────────────────────────┘                  │
│  │                                                                           │
│  ▼                                                                           │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐       │
│  │ GRAPH BUILDER   │    │  TEST GENERATOR  │    │   OUTPUTS         │       │
│  │                 │───▶│                  │───▶│                   │       │
│  │ • Nodes/Edges   │    │ • Positive Tests │    │ • Dependency Graph│       │
│  │ • Cycles        │    │ • Negative Tests │    │ • Test Cases      │       │
│  │ • Topological   │    │ • Boundary Tests │    │ • Sprint Order    │       │
│  │   Sort          │    │                  │    │ • Validation UI   │       │
│  │ • Critical Path │    │                  │    │                   │       │
│  └─────────────────┘    └──────────────────┘    └───────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Integration Points

CiRA integrates as **Layer 2.5** in the extraction pipeline, after Hierarchical Extraction but before Sprint Planning:

### 1. Hierarchical Story Extraction (Primary Integration)

**Location**: After `HierarchicalStoryExtractionService` extracts stories
**Trigger**: POST `/api/hierarchical/extract/{project_id}`

```
HierarchicalExtraction → CiRA Analysis → Dependency Graph → Sprint Planning
         │                    │                 │                │
    Stories extracted    Classify causal    Build edges     Topological
    from code             sentences        between stories   sprint order
```

**Implementation**:
```python
# In hierarchical_extraction_service.py, after stories extracted:
async def extract_stories(self, project_id: int) -> List[Story]:
    stories = await self._extract_from_code(project_id)

    # NEW: CiRA Causality Analysis
    if settings.ENABLE_CIRA_ANALYSIS:
        session = await cira_service.create_session(
            project_id=project_id,
            source_type="stories"
        )
        sentences = [s.description + " " + s.acceptance_criteria for s in stories]
        await cira_service.analyze_sentences(session.id, sentences)
        await cira_service.build_dependency_graph(session.id)

    return stories
```

### 2. Traceability Matrix Service

**Location**: Add causal dependency dimension to traceability
**Trigger**: POST `/api/traceability/{project_id}/matrix`

```
Business Rules → Epic/Feature/Story → CiRA Relations → Extended Matrix
      │                 │                   │               │
  Rule R001        Story S001 ──────▶ Story S002      R001 ↔ S001 → S002
                   (CAUSES)
```

**Implementation**:
```python
# In traceability_matrix_service.py:
async def build_matrix(self, project_id: int) -> TraceabilityMatrix:
    matrix = await self._build_base_matrix(project_id)

    # NEW: Add causal dependencies
    causal_relations = await cira_service.get_relations_for_project(project_id)
    for relation in causal_relations:
        matrix.add_dependency(
            source=relation.cause_source_id,
            target=relation.effect_source_id,
            type=relation.relation_type
        )

    return matrix
```

### 3. INVEST Validator

**Location**: Add dependency check to story validation
**Trigger**: POST `/api/validation/invest/{story_id}`

```
INVEST Criteria:
I - Independent  ──────▶ CiRA: Check if story has causal dependencies
N - Negotiable
V - Valuable
E - Estimable    ──────▶ CiRA: Add dependency overhead to estimate
S - Small
T - Testable     ──────▶ CiRA: Generate test cases from causal relations
```

**Implementation**:
```python
# In invest_validator_service.py:
async def validate_independent(self, story: Story) -> ValidationResult:
    # Check CiRA for blocking dependencies
    blocking = await cira_service.get_blocking_relations(story.id)

    if blocking:
        return ValidationResult(
            passed=False,
            message=f"Story blocked by: {[b.cause_source_id for b in blocking]}",
            suggestion="Consider splitting or reordering in sprint"
        )

    return ValidationResult(passed=True)
```

### 4. Sprint Planning Service

**Location**: Use CiRA dependency graph for sprint assignment
**Trigger**: POST `/api/sprints/auto-plan/{project_id}`

```
Sprint 1              Sprint 2              Sprint 3
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ S001 (root)    │───▶│ S003           │───▶│ S005           │
│ S002 (root)    │    │ S004           │    │ S006           │
└────────────────┘    └────────────────┘    └────────────────┘
      │                     │                     │
      ▼                     ▼                     ▼
 Topological Level 0   Level 1              Level 2
 (No dependencies)    (Depends on L0)    (Depends on L1)
```

**Implementation**:
```python
# In sprint_planning_service.py:
async def auto_plan_sprint(self, project_id: int) -> SprintPlan:
    # Get CiRA dependency graph
    graph = await cira_service.get_latest_graph(project_id)

    # Use topological order for sprint assignment
    sprint_order = graph.suggested_sprint_order

    for level, story_ids in enumerate(sprint_order):
        sprint = await self.get_or_create_sprint(project_id, f"Sprint {level + 1}")
        for story_id in story_ids:
            await self.assign_story_to_sprint(story_id, sprint.id)

    return SprintPlan(sprints=sprint_order, has_cycles=graph.has_cycles())
```

### 5. Test Generation (Tessa Agent)

**Location**: Generate acceptance tests from causal relations
**Trigger**: POST `/api/causality/sessions/{session_id}/tests`

```
Causal Relation:
"When user clicks submit (CAUSE) → form validates input (EFFECT)"

Generated Tests:
┌─────────────────────────────────────────────────────────────────┐
│ POSITIVE: Given form displayed, When user clicks submit,        │
│           Then form validates input                             │
│                                                                 │
│ NEGATIVE: Given form displayed, When user does NOT click submit,│
│           Then form does NOT validate input                     │
│                                                                 │
│ BOUNDARY: Given form with empty fields, When user clicks submit,│
│           Then validation shows error messages                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```sql
-- Session management
causal_sessions (
    id UUID PRIMARY KEY,
    project_id INT,
    extraction_id UUID,
    status VARCHAR(30),
    causal_count INT,
    non_causal_count INT,
    relation_count INT,
    avg_confidence FLOAT
)

-- Individual classifications
causal_classifications (
    id UUID PRIMARY KEY,
    session_id UUID FK,
    sentence TEXT,
    is_causal BOOLEAN,
    confidence FLOAT,
    markers JSONB
)

-- Extracted relations
causal_relations (
    id UUID PRIMARY KEY,
    session_id UUID FK,
    relation_type VARCHAR(30),  -- CAUSES, ENABLES, BLOCKS, DEPENDS_ON
    cause_text TEXT,
    effect_text TEXT,
    human_validated BOOLEAN,
    human_approved BOOLEAN
)

-- Dependency graphs
causal_dependency_graphs (
    id UUID PRIMARY KEY,
    session_id UUID FK,
    nodes JSONB,
    edges JSONB,
    critical_path JSONB,
    topological_order JSONB,
    suggested_sprint_order JSONB
)

-- Generated test cases
causal_test_cases (
    id UUID PRIMARY KEY,
    relation_id UUID FK,
    test_type VARCHAR(50),  -- positive, negative, boundary
    test_name VARCHAR(200),
    preconditions JSONB,
    trigger TEXT,
    expected_result TEXT,
    status VARCHAR(30),
    execution_result VARCHAR(30)
)
```

---

## API Endpoints

### Session Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/causality/sessions` | Create analysis session |
| GET | `/api/causality/sessions` | List sessions |
| GET | `/api/causality/sessions/{id}` | Get session details |
| DELETE | `/api/causality/sessions/{id}` | Delete session |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/causality/sessions/{id}/analyze` | Analyze sentences |
| GET | `/api/causality/sessions/{id}/classifications` | Get classifications |
| GET | `/api/causality/sessions/{id}/relations` | Get causal relations |

### Dependency Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/causality/sessions/{id}/graph` | Build dependency graph |
| GET | `/api/causality/sessions/{id}/graph` | Get graph data |
| GET | `/api/causality/sessions/{id}/graph/sprint-order` | Get sprint suggestions |

### Test Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/causality/sessions/{id}/tests` | Generate test cases |
| GET | `/api/causality/sessions/{id}/tests` | List test cases |
| POST | `/api/causality/tests/{id}/execute` | Record test execution |

### Validation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/causality/relations/{id}/validate` | Human validation |
| GET | `/api/causality/causal-markers` | List detection markers |

---

## Causal Markers (45)

The system detects these markers in requirements text:

```
if, when, because, since, therefore, hence, given, where, whose,
in order to, in the case of, due to, needed, require, required,
during, in case of, while, thus, as, except, forced by, only for,
within, after, whenever, which, before, allows, allow, unless,
prior to, as long as, depending on, depends on, result in,
increases, lead to, thereby, cause, in the event, once,
in such cases, throughout, improve, to that end, to this end,
so that, provided that, on condition that
```

---

## Relation Types

| Type | Example | Sprint Impact |
|------|---------|---------------|
| **CAUSES** | "Login enables dashboard access" | Effect after cause |
| **ENABLES** | "API setup allows frontend calls" | Enabler first |
| **BLOCKS** | "Missing auth blocks payment" | Blocker must resolve |
| **DEPENDS_ON** | "Reports depend on data import" | Dependency first |

---

## Integration with Existing Agents

| Agent | CiRA Integration |
|-------|------------------|
| **Peter** | Receives causal analysis during story refinement |
| **Felix** | Uses dependency graph for architecture decisions |
| **Paul** | Sprint planning with topological ordering |
| **Tessa** | Test generation from cause-effect pairs |
| **Quinn** | Quality gate: verify no circular dependencies |

---

## Configuration

```python
# app/config.py
class Settings:
    # CiRA settings
    CIRA_ENABLED: bool = True
    CIRA_MODEL_NAME: str = "bert-base-cased"
    CIRA_CONFIDENCE_THRESHOLD: float = 0.6
    CIRA_USE_POS_TAGS: bool = False
    CIRA_AUTO_BUILD_GRAPH: bool = True
    CIRA_AUTO_GENERATE_TESTS: bool = False  # Manual trigger recommended
```

---

## Week 124: Full BERT Integration ✅ COMPLETE

Week 124 delivers complete BERT model integration:

### Components Implemented

| Component | File | Description |
|-----------|------|-------------|
| **BERTCausalClassifier** | `bert_causal_classifier.py` | Full HuggingFace BERT integration |
| **BERTCausalityModel** | `bert_causal_classifier.py` | PyTorch BERT classifier model |
| **CausalityDataset** | `bert_causal_classifier.py` | Dataset class for training/inference |
| **POSTagger** | `bert_causal_classifier.py` | Optional spaCy POS tag features |

### Features

1. **BERT Model Loading**
   - HuggingFace transformers integration
   - Automatic device detection (CPU/CUDA/MPS)
   - Fine-tuned model loading from disk
   - Rule-based fallback when model unavailable

2. **Fine-tuning Pipeline**
   - Uses human-validated relations as training data
   - 80/20 train/validation split
   - AdamW optimizer with linear warmup
   - Automatic model saving with metadata

3. **Confidence Calibration**
   - Temperature scaling for probability calibration
   - Grid search for optimal temperature
   - Improves prediction reliability

4. **POS Tag Features**
   - Optional spaCy integration
   - Dependency pattern detection
   - Subordinate clause identification

### New API Endpoints (Week 124)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/causality/model/status` | Get BERT model status |
| POST | `/api/causality/model/load` | Explicitly load BERT model |
| POST | `/api/causality/model/fine-tune` | Fine-tune on project data |
| POST | `/api/causality/model/calibrate` | Calibrate confidence scores |

### Configuration Options

```python
# app/config.py
CIRA_ENABLED: bool = True
CIRA_MODEL_NAME: str = "bert-base-cased"
CIRA_MODEL_PATH: str = ""  # Path to fine-tuned model
CIRA_CONFIDENCE_THRESHOLD: float = 0.6
CIRA_USE_BERT: bool = True  # If False, use rule-based
CIRA_USE_POS_TAGS: bool = False  # Enable POS features
CIRA_DEVICE: str = "auto"  # auto, cpu, cuda, mps
CIRA_BATCH_SIZE: int = 16
CIRA_MAX_LENGTH: int = 128
CIRA_TEMPERATURE: float = 1.0  # Confidence calibration
```

### Database Tables (Migration 058)

```sql
-- Model metadata storage
bert_model_metadata (
    id, project_id, model_name, base_model, model_path,
    status, accuracy, f1_score, precision, recall,
    training_samples, validation_samples, epochs_trained,
    learning_rate, temperature, config, training_history
)

-- Training run history
bert_training_runs (
    id, model_id, project_id, run_type, status,
    started_at, completed_at, epochs, learning_rate,
    train_samples, val_samples, train_accuracy, val_accuracy,
    f1_score, optimal_temperature, error_message, config
)
```

---

## Week 125 Roadmap: Pipeline Integration

Next steps for Week 125:

1. **HierarchicalStoryExtractionService Integration**
   - Auto-analyze stories after extraction
   - Build dependency graphs automatically
   - Suggest sprint ordering

2. **Traceability Matrix Integration**
   - Add causal dependencies to matrix
   - Show cause-effect chains

3. **INVEST Validator Integration**
   - Check story independence via causal graph
   - Add dependency overhead to estimates

---

**Related Documentation**:
- [Hierarchical Extraction](./deep-extraction-pipeline.md)
- [Traceability Matrix](./traceability-matrix.md)
- [Sprint Planning](./sprint-planning.md)
- [INVEST Validation](./invest-validation.md)
