# A/B Testing Framework Architecture

**Status:** Week 51 COMPLETE (25 Nov 2025)
**Doel:** Data-driven agent evolution through multi-variant experimentation
**Leveraged:** 2,150+ lines production code, 53 comprehensive tests, 9 API endpoints

---

## Design Filosofie

**"Measure, Learn, Improve"** - Continuous agent evolution through:
1. Multi-variant experimentation (control vs treatment)
2. Statistical significance testing (p-values, confidence intervals)
3. Automatic winner detection and rollout
4. Performance tracking over time

---

## High-Level Architecture

```
+---------------------------------------------------------------------+
|                     A/B TESTING FRAMEWORK                            |
|                                                                      |
|  +------------------+   +------------------+   +----------------+    |
|  | EXPERIMENT       |   | TRAFFIC          |   | STATISTICAL    |    |
|  | MANAGEMENT       |   | ALLOCATION       |   | ANALYSIS       |    |
|  |                  |   |                  |   |                |    |
|  | - Create         |   | - Deterministic  |   | - P-values     |    |
|  | - Start/Pause    |   |   Hash           |   | - Confidence   |    |
|  | - Complete       |   | - Sticky         |   |   Intervals    |    |
|  | - Winner         |   |   Assignment     |   | - Winner       |    |
|  |   Declaration    |   | - Weighted       |   |   Detection    |    |
|  |                  |   |   Random         |   |                |    |
|  +--------+---------+   +--------+---------+   +-------+--------+    |
|           |                      |                     |             |
|           +----------------------+---------------------+             |
|                                  |                                   |
|  +---------------------------------------------------------------+  |
|  |                     RESULT TRACKING                            |  |
|  |  - Success/failure logging                                     |  |
|  |  - Metrics: success_rate, execution_time, quality_score        |  |
|  |  - Work type classification                                    |  |
|  +---------------------------------------------------------------+  |
|                                  |                                   |
|  +---------------------------------------------------------------+  |
|  |                  EVOLUTION METRICS                             |  |
|  |  - Performance tracking per agent                              |  |
|  |  - Trend analysis (improving/stable/declining)                 |  |
|  |  - Daily/weekly aggregation                                    |  |
|  |  - Cross-agent comparison                                      |  |
|  |  - ChromaDB milestone storage                                  |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## Database Schema (3 Nieuwe Tables)

**Migration 011** - `846bf79a97f4_add_ab_testing_tables.py`

```sql
-- Experiments table
CREATE TABLE experiments (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    feature_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    winner_variant_id UUID,
    extra_metadata JSONB DEFAULT '{}',
    CONSTRAINT check_experiment_status
        CHECK (status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED'))
);

-- Experiment variants table
CREATE TABLE experiment_variants (
    id UUID PRIMARY KEY,
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    variant_name VARCHAR(100) NOT NULL,
    traffic_percentage FLOAT NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}',
    is_control BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT check_traffic_percentage
        CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100)
);

-- Experiment results table
CREATE TABLE experiment_results (
    id UUID PRIMARY KEY,
    variant_id UUID REFERENCES experiment_variants(id) ON DELETE CASCADE,
    task_id VARCHAR(100) NOT NULL,
    work_type VARCHAR(50),
    success BOOLEAN NOT NULL,
    metrics_json JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP NOT NULL
);
```

---

## Service Layer (2 Services)

### ABTestingService (`ab_testing_service.py` - 550 lines)

**Experiment Lifecycle:**
- `create_experiment()` - Setup with variants (validates traffic = 100%, 1 control)
- `start_experiment()` - Activate (DRAFT -> ACTIVE)
- `pause_experiment()` - Temporarily stop (ACTIVE -> PAUSED)
- `complete_experiment()` - Declare winner (ACTIVE -> COMPLETED)

**Traffic Allocation:**
- `allocate_traffic()` - Deterministic sticky assignment
- SHA256 hash(task_id + experiment_id) -> consistent variant
- Weighted random selection based on traffic_percentage
- Same task always gets same variant

**Statistical Analysis:**
- `analyze_experiment()` - Complete statistical report
- Confidence intervals (95%) using normal approximation
- P-value calculation (two-proportion z-test)
- Winner detection with significance threshold (p < 0.05)
- Minimum samples enforcement (30+ per variant)

### EvolutionMetricsService (`evolution_metrics_service.py` - 500 lines)

**Agent Performance:**
- `get_agent_performance()` - Comprehensive metrics
- total_experiments, active, completed counts
- average_success_rate, improvement_rate
- best_variant identification

**Trend Analysis:**
- `analyze_trends()` - Time series analysis
- Daily values with trend direction (improving/stable/declining)
- Standard deviation and percentage change

**ChromaDB Integration:**
- `store_evolution_milestone()` - Save significant achievements
- `retrieve_evolution_milestones()` - Query by agent/type
- Milestone types: major_improvement (>=20%), improvement_threshold (>=10%), high_success_rate (>=95%)

---

## REST API (9 Endpoints)

**Router:** `/api/evolution/*` (ab_testing.py - 650 lines)

```
POST   /api/evolution/experiments              - Create experiment
GET    /api/evolution/experiments              - List experiments
GET    /api/evolution/experiments/{id}         - Get experiment
PUT    /api/evolution/experiments/{id}/start   - Start experiment
PUT    /api/evolution/experiments/{id}/pause   - Pause experiment
PUT    /api/evolution/experiments/{id}/complete - Complete with winner
POST   /api/evolution/experiments/{id}/results - Log result
GET    /api/evolution/experiments/{id}/analysis - Statistical analysis
POST   /api/evolution/experiments/{id}/allocate - Traffic allocation
```

---

## Experiment Lifecycle

```
+----------+
|  DRAFT   | <- create_experiment()
+----+-----+
     | start_experiment()
     v
+----------+      pause_experiment()      +----------+
|  ACTIVE  | <-------------------------> |  PAUSED  |
+----+-----+                              +----------+
     | complete_experiment(winner_id)
     v
+----------+
|COMPLETED |
+----------+
```

---

## Traffic Allocation Logic

**Deterministic Sticky Assignment:**
```python
hash_value = SHA256(f"{task_id}-{experiment_id}") % 100  # 0-99
cumulative = 0
for variant in sorted(variants):
    cumulative += variant.traffic_percentage
    if hash_value < cumulative:
        return variant
```

**Properties:**
- Same task always gets same variant (sticky)
- Distribution matches traffic percentages over many tasks
- No external state required (hash is deterministic)
- Works across restarts and deployments

---

## Statistical Analysis

**Confidence Intervals (95%):**
- Normal approximation to binomial distribution
- Z-score = 1.96 for 95% confidence
- Standard error: `sqrt(p*(1-p)/n)`
- Margin: `z * standard_error`

**P-Value Calculation:**
- Two-proportion z-test
- Null hypothesis: variant_rate == control_rate
- Pooled proportion across both groups
- Significant if p < 0.05

**Winner Detection:**
- Minimum 30 samples per variant
- P-value < 0.05 (statistically significant)
- Improvement > 0 (better than control)
- Consensus level = 1 - p_value

---

## Testing Coverage (53 Tests)

**Unit Tests** (`test_ab_testing_service.py` - 18 tests):
- Experiment creation validation
- Lifecycle transitions
- Traffic allocation
- Statistical analysis

**Integration Tests** (`test_ab_testing_api.py` - 20 tests):
- API endpoint validation
- Request/response schemas
- Error handling

**Evolution Metrics Tests** (`test_evolution_metrics.py` - 15 tests):
- Agent performance tracking
- Trend analysis
- ChromaDB integration

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Experiment Velocity** | 10+ experiments/week | Experiment creation rate |
| **Statistical Confidence** | >95% consensus | P-value < 0.05 |
| **Improvement Rate** | +15% average | Variant vs control |
| **Winner Accuracy** | >90% stable | Post-rollout performance |
| **Sample Size** | 30+ per variant | Before analysis |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Continuous Evolution](./continuous-evolution.md) - Trend analysis and rollout
- [Self-Evolution Layer](./self-evolution.md) - Agent learning integration
