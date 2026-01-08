# LLM Council Architecture

**Status:** Week 52 COMPLETE
**Design Concept:** Multi-model consensus decision making via democratic voting + peer review

---

## Overview

When Felix (or other agents) face critical architecture decisions, they consult the **LLM Council** - 6 local Ollama models working together to reach consensus through a 3-stage democratic process.

---

## Design Filosofie

**"Wisdom of the Crowd"** - Complex decisions benefit from multiple perspectives:
- No single model has all the answers
- Peer review reduces individual biases
- Consensus indicates confidence
- Dissenting opinions are valuable signals

---

## High-Level Architecture

```
+---------------------------------------------------------------------+
|                     LLM COUNCIL SYSTEM                               |
|                                                                      |
|  +------------------+   +------------------+   +----------------+    |
|  | STAGE 1: QUERY   |   | STAGE 2: REVIEW  |   | STAGE 3:       |    |
|  |                  |   |                  |   | SYNTHESIS      |    |
|  | - Parallel query |   | - Blind peer     |   | - Chairman     |    |
|  |   6 models       |   |   review         |   |   synthesis    |    |
|  | - asyncio.gather |   | - N x (N-1)      |   | - Consensus    |    |
|  | - Confidence     |   |   reviews        |   |   calculation  |    |
|  |   scores         |   | - 4-dim scoring  |   | - Outlier      |    |
|  |                  |   |                  |   |   detection    |    |
|  +--------+---------+   +--------+---------+   +-------+--------+    |
|           |                      |                     |             |
|           +----------------------+---------------------+             |
|                                  |                                   |
|  +---------------------------------------------------------------+  |
|  |                    DATABASE (4 TABLES)                         |  |
|  |  - council_sessions      (question + context + status)         |  |
|  |  - council_responses     (6 model responses + confidence)      |  |
|  |  - council_reviews       (NxN-1 peer reviews + 4 scores)       |  |
|  |  - council_decisions     (final decision + consensus %)        |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## 6 Council Models (Roles & Weights)

| Model | Role | Weight | Specialty |
|-------|------|--------|-----------|
| **deepseek-r1** | Chairman | 2.0 | Reasoning & analysis |
| **qwen2.5-coder:7b** | Technical | 1.5 | Code generation |
| **codellama** | Implementation | 1.5 | Debugging & patterns |
| **mistral** | Documentation | 1.0 | Clarity & communication |
| **qwen2.5:7b** | Planning | 1.0 | Strategic thinking |
| **llama3.2** | Generalist | 1.0 | Broad knowledge |

**Weight Significance:** Chairman has 2x influence in final synthesis

---

## 3-Stage Process

### Stage 1: Parallel Query (Response Collection)

```python
async def query_all_models(session_id: UUID) -> List[CouncilResponse]:
    """Query all 6 models concurrently."""
    prompt = build_prompt(session.question, session.context)

    # Parallel execution (6 models at once)
    tasks = [
        query_single_model(model_name, prompt, session_id)
        for model_name in MODELS
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return successful_responses
```

**Output:** 6 model responses with confidence scores (0-1)

### Stage 2: Blind Peer Review (Anonymous Evaluation)

```python
async def peer_review(session_id: UUID) -> List[CouncilReview]:
    """Each model reviews all other models' responses (blind)."""
    # N x (N-1) reviews (e.g., 6 x 5 = 30 reviews)
    review_tasks = []
    for reviewer_model in MODELS:
        for response in responses:
            if response.model != reviewer_model:
                # Anonymize: reviewer doesn't know which model wrote response
                review_tasks.append(
                    review_single_response(reviewer_model, response)
                )

    reviews = await asyncio.gather(*review_tasks)
    return reviews
```

**4-Dimension Scoring (0-10 each):**
- **Accuracy** - Technical correctness
- **Completeness** - Addresses all requirements
- **Clarity** - Communication quality
- **Feasibility** - Can be implemented

**Output:** 30 peer reviews (6 models x 5 others each)

### Stage 3: Chairman Synthesis (Consensus Decision)

```python
async def synthesize(session_id: UUID, chairman: str = "deepseek-r1") -> CouncilDecision:
    """Chairman synthesizes final decision based on responses + reviews."""
    # Calculate aggregate scores for each response
    response_scores = calculate_aggregate_scores(responses, reviews)

    # Calculate consensus level (0-100%)
    consensus = calculate_consensus(responses, response_scores)

    # Detect outliers (>2sigma from mean)
    dissenting = detect_outliers(responses, response_scores)

    # Chairman synthesizes final decision
    decision = await query_chairman(chairman, prompt)
    return CouncilDecision(
        final_decision=decision,
        consensus_level=consensus,
        dissenting_opinions=dissenting,
    )
```

**Output:** Final decision with consensus % and dissenting opinions

---

## Consensus Calculation Algorithm

```python
def calculate_consensus(responses: List[CouncilResponse],
                       scores: Dict[str, float]) -> float:
    """
    Consensus based on variance in:
    1. Model confidence values (60% weight)
    2. Peer review scores (40% weight)

    Lower variance = higher consensus
    """
    # Confidence variance
    confidences = [r.confidence for r in responses]
    conf_std = std_dev(confidences)
    conf_consensus = max(0, 100 * (1 - conf_std / 0.5))

    # Score variance
    score_std = std_dev(scores.values())
    score_consensus = max(0, 100 * (1 - score_std / 5.0))

    # Weighted average
    return conf_consensus * 0.6 + score_consensus * 0.4
```

**Consensus Levels:**
- 75-100%: Strong agreement (trust high)
- 50-75%: Moderate agreement (proceed with caution)
- 0-50%: Low agreement (investigate dissent)

---

## Outlier Detection (Dissenting Opinions)

```python
def detect_outliers(responses: List[CouncilResponse],
                   scores: Dict[str, float]) -> List[str]:
    """Detect responses >2sigma from mean (statistical outliers)."""
    mean_score = mean(scores.values())
    std = std_dev(scores.values())

    outliers = []
    for response_id, score in scores.items():
        z_score = (score - mean_score) / std
        if abs(z_score) > 2.0:  # >2 standard deviations
            outliers.append(response_id)

    return outliers
```

**Why Track Dissent?** Outliers often reveal important edge cases or risks

---

## Felix Integration (Decision Thresholds)

```typescript
class FelixCouncilIntegration {
    shouldUseCouncil(complexity: number, impact: 'low' | 'medium' | 'high'): boolean {
        // HIGH impact -> always use council
        if (impact === 'high') return true;

        // MEDIUM impact + high complexity -> use council
        if (impact === 'medium' && complexity >= 7) return true;

        // LOW impact -> Felix decides alone
        return false;
    }
}
```

**Decision Logic:**
- **Simple decisions:** Felix alone (fast, efficient)
- **Critical decisions:** Consult council (wisdom of crowd)
- **Graceful fallback:** If council unavailable, Felix proceeds solo

---

## Database Schema (Migration 012)

```sql
-- Session tracking
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}',
    decision_type VARCHAR(50) NOT NULL CHECK (decision_type IN
        ('architecture', 'planning', 'quality', 'generation')),
    agent_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN
        ('pending', 'reviewing', 'complete')),
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

-- Model responses (Stage 1)
CREATE TABLE council_responses (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES council_sessions(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    response_text TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Peer reviews (Stage 2)
CREATE TABLE council_reviews (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES council_sessions(id) ON DELETE CASCADE,
    reviewer_model VARCHAR(100) NOT NULL,
    response_id UUID NOT NULL REFERENCES council_responses(id) ON DELETE CASCADE,
    accuracy_score FLOAT NOT NULL CHECK (accuracy_score >= 0 AND accuracy_score <= 10),
    completeness_score FLOAT NOT NULL CHECK (completeness_score >= 0 AND completeness_score <= 10),
    clarity_score FLOAT NOT NULL CHECK (clarity_score >= 0 AND clarity_score <= 10),
    feasibility_score FLOAT NOT NULL CHECK (feasibility_score >= 0 AND feasibility_score <= 10),
    comments TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Final decisions (Stage 3)
CREATE TABLE council_decisions (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES council_sessions(id) ON DELETE CASCADE UNIQUE,
    chairman_model VARCHAR(100) NOT NULL,
    final_decision TEXT NOT NULL,
    reasoning TEXT,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    consensus_level FLOAT NOT NULL CHECK (consensus_level >= 0 AND consensus_level <= 100),
    dissenting_opinions TEXT[],
    model_weights JSONB,
    aggregate_scores JSONB,
    created_at TIMESTAMP NOT NULL
);
```

---

## REST API (8 Endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/council/sessions` | Create new session |
| GET | `/api/council/sessions` | List sessions (filtered, paginated) |
| GET | `/api/council/sessions/{id}` | Get session details + relationships |
| POST | `/api/council/sessions/{id}/query` | Execute Stage 1 (query models) |
| POST | `/api/council/sessions/{id}/review` | Execute Stage 2 (peer review) |
| POST | `/api/council/sessions/{id}/synthesize` | Execute Stage 3 (synthesis) |
| GET | `/api/council/sessions/{id}/decision` | Get final decision |
| POST | `/api/council/quick` | **All 3 stages in one call** |

---

## Use Cases

### Example 1: Microservices Architecture Decision
```
Question: "Should we use microservices or monolith for e-commerce platform?"
Context: {requirements: ['scalability', 'reliability'], constraints: ['budget', 'team-size']}
Complexity: 8 (high)
Impact: high (affects core + multiple services)

-> Council consulted (6 models respond)
-> 30 peer reviews generated
-> Consensus: 82% (strong agreement)
-> Decision: "Adopt microservices with API gateway"
-> Dissenting: 1 model (budget concerns noted)
```

### Example 2: Simple Logging Feature
```
Question: "Add logging to user endpoint?"
Context: {requirements: ['observability']}
Complexity: 3 (low)
Impact: low (reversible, single service)

-> Council NOT consulted (below threshold)
-> Felix decides alone
-> Decision: "Add structured logging with correlation IDs"
```

---

## Production Metrics (Week 52 Output)

| Metric | Value |
|--------|-------|
| **Production Code** | 3,300+ lines |
| **Tests** | 47 comprehensive tests |
| **API Endpoints** | 8 new endpoints |
| **Database Tables** | 4 new tables |
| **Models in Council** | 6 local Ollama models |
| **Consensus Algorithm** | Variance-based (confidence + scores) |
| **Parallel Execution** | asyncio.gather (6 concurrent) |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Decision Quality** | +20% accuracy | Council vs solo decisions |
| **Consensus Reliability** | >80% when >70% | Post-decision validation |
| **Execution Speed** | <5 min total | Full 3-stage process |
| **Model Availability** | >95% uptime | Ollama health checks |
| **Felix Adoption** | 50%+ critical decisions | Felix usage logs |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Project Profiles](./project-profiles.md) - Profile-adjusted thresholds
- [A/B Testing Framework](./ab-testing.md) - Experimentation for council parameters
