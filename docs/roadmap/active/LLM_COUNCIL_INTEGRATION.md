# LLM COUNCIL INTEGRATION PLAN

**Status:** PLANNED
**Priority:** HIGH - Quality Critical
**Implementation:** Week 51-52 (parallel track)
**Based on:** github.com/zeeneddie/llm-council concept

---

## 🎯 Doel

Implementeer multi-LLM consensus systeem voor kritieke beslissingen in:
- Architectuur & Design
- Epic/Feature/Story/Task generatie
- Project opzet & planning
- Kwaliteitsbeoordelingen

**Kernprincipe:** "Wisdom of crowds" met lokale Ollama modellen

---

## 📊 LLM Council Pattern

### 3-Stage Consensus Process

```
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 1: RESPONSE                        │
│  Query → 5-6 lokale modellen → Verzamel individuele answers│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 2: PEER REVIEW                     │
│  Modellen beoordelen elkaars responses (blind/anonymous)   │
│  Ranking: Accuracy, Completeness, Clarity, Feasibility     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 3: SYNTHESIS                       │
│  Chairman model (deepseek-r1) synthesizes final decision   │
│  Incorporates best elements from all perspectives          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Council Samenstelling (6 Lokale Modellen)

| Model | Role | Specialty | Voting Weight |
|-------|------|-----------|---------------|
| **deepseek-r1:latest** | Chairman | Reasoning & synthesis | 2.0 |
| **qwen2.5-coder:7b** | Technical Expert | Code architecture | 1.5 |
| **codellama:latest** | Implementation | Practical feasibility | 1.5 |
| **mistral:latest** | Documentation | Clarity & completeness | 1.0 |
| **qwen2.5:7b** | Planning | Project structure | 1.0 |
| **llama3.2:latest** | Quality | Best practices | 1.0 |

**Total Weight:** 8.0 (normalized to 1.0 for percentage)

---

## 🎭 Use Cases & Triggers

### 1. Architecture Decisions

**Trigger:** Felix agent needs to make architecture choice
**Council Question Types:**
- "Should we use microservices or monolith for feature X?"
- "Best database design for Y requirements?"
- "API design: REST vs GraphQL for Z use case?"

**Example Council Flow:**
```python
question = "Architecture choice for user authentication system"
context = {
    "requirements": ["OAuth2", "JWT", "Multi-tenant"],
    "constraints": ["Must scale to 100K users", "Budget: low"],
    "current_stack": ["FastAPI", "PostgreSQL"]
}

# Stage 1: Each model proposes solution
responses = await council.query_all_models(question, context)

# Stage 2: Models peer review
reviews = await council.peer_review(responses)

# Stage 3: Chairman synthesis
final_decision = await council.synthesize(
    question, responses, reviews, chairman="deepseek-r1"
)
```

### 2. Epic/Feature/Story Generation

**Trigger:** Peter/Felix creating project structure
**Council Question Types:**
- "Break down feature X into epics"
- "Are these user stories complete and testable?"
- "Task dependencies: correct order?"

**Validation Points:**
- Story completeness (all INVEST criteria)
- Acceptance criteria clarity
- Effort estimation reasonableness
- Technical feasibility

### 3. Project Planning

**Trigger:** Paul agent creating project plan
**Council Question Types:**
- "Is this 6-day sprint realistic?"
- "Resource allocation optimal?"
- "Risk mitigation strategy complete?"

### 4. Quality Gate Decisions

**Trigger:** Quinn agent evaluating quality
**Council Question Types:**
- "Is this security vulnerability critical?"
- "Code quality: acceptable for production?"
- "Technical debt: pay now or later?"

**Override Scenarios:**
- Quality gate fails but team wants to proceed
- Council provides risk assessment + recommendation

---

## 🏗️ Technical Architecture

### Database Schema (3 nieuwe tables)

```sql
-- Council sessions tracking
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    context JSONB NOT NULL,
    decision_type VARCHAR(50),  -- architecture, planning, quality, generation
    agent_id VARCHAR(50),       -- Requesting agent
    status VARCHAR(20),         -- pending, reviewing, complete
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Individual model responses
CREATE TABLE council_responses (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    model_name VARCHAR(100),
    response_text TEXT,
    confidence FLOAT,           -- 0.0-1.0
    reasoning TEXT,             -- Model's explanation
    created_at TIMESTAMP
);

-- Peer reviews (models reviewing each other)
CREATE TABLE council_reviews (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    reviewer_model VARCHAR(100),
    reviewed_response_id UUID REFERENCES council_responses(id),
    accuracy_score FLOAT,       -- 0-10
    completeness_score FLOAT,   -- 0-10
    clarity_score FLOAT,        -- 0-10
    feasibility_score FLOAT,    -- 0-10
    comments TEXT,
    created_at TIMESTAMP
);

-- Final synthesis
CREATE TABLE council_decisions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    chairman_model VARCHAR(100),
    final_decision TEXT,
    confidence FLOAT,
    consensus_level FLOAT,      -- 0-100% agreement
    dissenting_opinions TEXT[], -- Minority views
    created_at TIMESTAMP
);
```

### Python Service Layer

**File:** `backend/app/services/llm_council_service.py` (~600 lines)

```python
class LLMCouncilService:
    """
    Multi-LLM consensus decision making service.
    """

    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.models = {
            "deepseek-r1:latest": {"weight": 2.0, "role": "chairman"},
            "qwen2.5-coder:7b": {"weight": 1.5, "role": "technical"},
            "codellama:latest": {"weight": 1.5, "role": "implementation"},
            "mistral:latest": {"weight": 1.0, "role": "documentation"},
            "qwen2.5:7b": {"weight": 1.0, "role": "planning"},
            "llama3.2:latest": {"weight": 1.0, "role": "quality"}
        }

    async def create_session(
        self,
        question: str,
        context: dict,
        decision_type: str,
        agent_id: str
    ) -> CouncilSession:
        """Start new council session."""
        pass

    async def query_all_models(
        self,
        session_id: str
    ) -> list[CouncilResponse]:
        """Stage 1: Query all models in parallel."""
        # Use asyncio.gather for concurrent Ollama calls
        pass

    async def peer_review(
        self,
        session_id: str
    ) -> list[CouncilReview]:
        """Stage 2: Models review each other (blind)."""
        # Anonymize responses before review
        # Each model reviews all others
        pass

    async def synthesize(
        self,
        session_id: str,
        chairman_model: str = "deepseek-r1:latest"
    ) -> CouncilDecision:
        """Stage 3: Chairman synthesizes final decision."""
        pass

    def calculate_consensus(
        self,
        reviews: list[CouncilReview]
    ) -> float:
        """Calculate consensus level (0-100%)."""
        # Based on review score variance
        pass

    def detect_outliers(
        self,
        responses: list[CouncilResponse]
    ) -> list[str]:
        """Find minority/dissenting opinions."""
        pass
```

### REST API Endpoints

**File:** `backend/app/api/llm_council.py` (~400 lines)

```python
# POST /api/council/sessions - Create new council session
# GET  /api/council/sessions/{id} - Get session details
# POST /api/council/sessions/{id}/query - Execute Stage 1
# POST /api/council/sessions/{id}/review - Execute Stage 2
# POST /api/council/sessions/{id}/synthesize - Execute Stage 3
# GET  /api/council/sessions/{id}/decision - Get final decision
# GET  /api/council/statistics - Council performance stats
# POST /api/council/quick - All 3 stages in one call
```

---

## 🔄 Integration with Existing Agents

### Felix (Architecture)

**Before Council:**
```typescript
// Felix makes solo decision
const architecture = await felix.proposeArchitecture(requirements);
```

**With Council:**
```typescript
// Felix triggers council for critical decision
const councilDecision = await llmCouncil.decide({
    question: "Best architecture for user auth system?",
    context: {
        requirements: ["OAuth2", "JWT", "Multi-tenant"],
        constraints: felix.constraints,
        current_stack: felix.techStack
    },
    decision_type: "architecture",
    agent_id: "felix"
});

// Felix implements council decision
const architecture = await felix.implement(councilDecision);
```

### Peter (Requirements)

**Council Integration:**
```typescript
// Peter validates requirements completeness via council
const validation = await llmCouncil.decide({
    question: "Are these user stories complete and testable?",
    context: {
        stories: peter.userStories,
        acceptance_criteria: peter.acceptanceCriteria
    },
    decision_type: "generation",
    agent_id: "peter"
});

if (validation.consensus_level < 0.7) {
    // Low consensus → stories need work
    peter.refineStories(validation.dissenting_opinions);
}
```

### Quinn (Quality)

**Council Override Mechanism:**
```typescript
// Quinn quality gate fails, but team wants to proceed
const riskAssessment = await llmCouncil.decide({
    question: "Risk assessment for proceeding despite quality gate failure?",
    context: {
        failed_checks: quinn.failedChecks,
        business_urgency: "HIGH",
        mitigation_plan: team.mitigationPlan
    },
    decision_type: "quality",
    agent_id: "quinn"
});

if (riskAssessment.consensus_level > 0.8) {
    // High consensus → safe to override
    quinn.approveWithConditions(riskAssessment.final_decision);
}
```

---

## 📅 Implementation Timeline

### Week 51: Foundation (parallel met A/B Testing)

**Day 1-2: Database & Models**
- [ ] Council session models (4 tables)
- [ ] Alembic migration
- [ ] TypeScript types

**Day 3: Core Service**
- [ ] LLMCouncilService class
- [ ] Ollama integration (async concurrent calls)
- [ ] Stage 1: query_all_models()

**Day 4: Peer Review Logic**
- [ ] Stage 2: peer_review()
- [ ] Response anonymization
- [ ] Review scoring algorithms

**Day 5: Synthesis & API**
- [ ] Stage 3: synthesize()
- [ ] REST API endpoints (8 endpoints)
- [ ] Basic testing

### Week 52: Agent Integration

**Day 1: Felix Integration**
- [ ] Architecture decision hooks
- [ ] Council trigger logic
- [ ] Decision implementation

**Day 2: Peter/Paul Integration**
- [ ] Requirements validation
- [ ] Planning decisions
- [ ] Story completeness checks

**Day 3: Quinn Integration**
- [ ] Quality gate override mechanism
- [ ] Risk assessment integration
- [ ] Mitigation recommendations

**Day 4: Dashboard UI**
- [ ] Council session viewer
- [ ] Response comparison table
- [ ] Consensus visualization

**Day 5: Testing & Docs**
- [ ] 30+ integration tests
- [ ] Performance benchmarks
- [ ] Documentation updates

---

## 🎯 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Consensus Accuracy** | >80% | Final decision quality |
| **Response Time** | <30s | Full 3-stage cycle |
| **Model Availability** | 95%+ | Ollama uptime |
| **Override Safety** | 0 incidents | No bad overrides |
| **Agent Satisfaction** | >4/5 | Agent feedback score |

---

## 🚨 Guardrails & Safety

### When to Use Council

**USE COUNCIL:**
- ✅ Architecture decisions (breaking changes)
- ✅ Quality gate overrides (risk assessment)
- ✅ Sprint planning (resource allocation)
- ✅ Epic/Feature breakdown (complexity > 5)

**DON'T USE COUNCIL:**
- ❌ Simple code formatting decisions
- ❌ Obvious bug fixes
- ❌ Low-risk implementation details
- ❌ Time-sensitive emergencies (<5 min)

### Thresholds

```python
COUNCIL_THRESHOLDS = {
    "high_consensus": 0.8,      # >80% agreement → proceed
    "medium_consensus": 0.6,    # 60-80% → review carefully
    "low_consensus": 0.4,       # <60% → escalate to human
    "min_models": 4,            # Minimum models for valid decision
    "timeout": 60,              # Max seconds per stage
}
```

### Escalation

**Low Consensus (<60%):**
1. Log dissenting opinions
2. Notify agent of disagreement
3. Suggest human review
4. Don't auto-proceed

**Model Failure:**
- If <4 models respond → abort council
- Use agent's solo decision as fallback
- Log incident for review

---

## 📊 Expected Impact

### Before Council

| Scenario | Outcome |
|----------|---------|
| Architecture choice | Single model opinion |
| Quality override | Manual human decision |
| Planning accuracy | ~70% estimation error |
| Story completeness | 60% missing criteria |

### After Council

| Scenario | Outcome |
|----------|---------|
| Architecture choice | 5-6 model consensus |
| Quality override | Risk-assessed decision |
| Planning accuracy | ~50% estimation error (-20%) |
| Story completeness | 85% complete criteria (+25%) |

---

## 🔗 Dependencies

**Existing Systems:**
- Ollama (6 models running)
- Agent service layer
- Quality gate system
- Experience store (ChromaDB)

**New Dependencies:**
- None! (Pure Python + existing stack)

---

## 📝 Configuration

**File:** `backend/app/config/council_config.py`

```python
COUNCIL_CONFIG = {
    "models": {
        "deepseek-r1:latest": {
            "weight": 2.0,
            "role": "chairman",
            "timeout": 30,
            "max_retries": 2
        },
        # ... andere modellen
    },
    "thresholds": COUNCIL_THRESHOLDS,
    "decision_types": {
        "architecture": ["deepseek-r1", "qwen2.5-coder", "codellama"],
        "planning": ["deepseek-r1", "qwen2.5", "mistral"],
        "quality": ["deepseek-r1", "qwen2.5-coder", "llama3.2"],
        "generation": ["qwen2.5-coder", "mistral", "qwen2.5"]
    }
}
```

---

**Created:** 2025-11-25
**Author:** Eddie + Claude Code
**Status:** READY FOR IMPLEMENTATION 🚀
**Priority:** HIGH - Improves decision quality across all agents
