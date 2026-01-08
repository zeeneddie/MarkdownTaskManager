# WEEK 52 IMPLEMENTATION PLAN: LLM Council Multi-Model Decision Making

**Week:** 52 (2025-12-02 - 2025-12-06)
**Focus:** LLM Council Foundation + Initial Agent Integration
**Effort:** 40 uren (5 dagen × 8u)
**Status:** Week 51 COMPLETE ✅ → Week 52 IN PLANNING

---

## 🎯 Week 52 Doel

**Implementeer multi-LLM consensus systeem** voor kritieke beslissingen:
- Architecture & design decisions
- Epic/Feature/Story generation validation
- Quality gate override assessments
- Project planning & resource allocation

**3-Stage Process:**
1. **Response** - Query 6 lokale Ollama modellen parallel
2. **Peer Review** - Modellen beoordelen elkaar (blind/anonymous)
3. **Synthesis** - Chairman model (deepseek-r1) creëert consensus

---

## 📊 Week 52 Overview

| Day | Focus | Hours | Output |
|-----|-------|-------|--------|
| 1 | Database + Models + TypeScript | 8h | 4 tables, migration 012, types (~500 lines) |
| 2 | Core Service (Stage 1: Response) | 8h | LLMCouncilService + Ollama integration (~400 lines) |
| 3 | Peer Review + Synthesis (Stage 2+3) | 8h | Review & synthesis logic (~350 lines) |
| 4 | REST API + Felix Integration | 8h | 8 endpoints + agent hooks (~500 lines) |
| 5 | Testing + Dashboard UI + Docs | 8h | 25+ tests + UI (~600 lines) |
| **TOTAL** | **LLM Council Complete** | **40h** | **~2,350 lines** |

---

## 🗓️ Day 1 (Monday): Database Foundation (8h)

### Deliverables
- 4 SQLAlchemy models
- Alembic migration 012
- TypeScript type definitions
- Migration testing

### Tasks

#### 1. Database Models (4h)

**File:** `backend/app/models/llm_council.py` (~300 lines)

**4 Models:**

```python
class CouncilSession(Base):
    """Council session for multi-LLM decision making."""
    __tablename__ = "council_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    context = Column(JSONB, nullable=False, default={})
    decision_type = Column(String(50), nullable=False)  # architecture, planning, quality, generation
    agent_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, reviewing, complete
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship("CouncilResponse", back_populates="session", cascade="all, delete-orphan")
    reviews = relationship("CouncilReview", back_populates="session", cascade="all, delete-orphan")
    decision = relationship("CouncilDecision", back_populates="session", uselist=False, cascade="all, delete-orphan")

class CouncilResponse(Base):
    """Individual model response in a council session."""
    __tablename__ = "council_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("council_sessions.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("CouncilSession", back_populates="responses")
    reviews_received = relationship("CouncilReview", back_populates="reviewed_response", cascade="all, delete-orphan")

class CouncilReview(Base):
    """Peer review from one model to another's response."""
    __tablename__ = "council_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("council_sessions.id", ondelete="CASCADE"), nullable=False)
    reviewer_model = Column(String(100), nullable=False)
    reviewed_response_id = Column(UUID(as_uuid=True), ForeignKey("council_responses.id", ondelete="CASCADE"), nullable=False)
    accuracy_score = Column(Float, nullable=False)      # 0-10
    completeness_score = Column(Float, nullable=False)  # 0-10
    clarity_score = Column(Float, nullable=False)       # 0-10
    feasibility_score = Column(Float, nullable=False)   # 0-10
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("CouncilSession", back_populates="reviews")
    reviewed_response = relationship("CouncilResponse", back_populates="reviews_received")

class CouncilDecision(Base):
    """Final synthesized decision from chairman model."""
    __tablename__ = "council_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("council_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    chairman_model = Column(String(100), nullable=False)
    final_decision = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    consensus_level = Column(Float, nullable=False)  # 0-100% agreement
    dissenting_opinions = Column(ARRAY(Text), nullable=True)  # Minority views
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationship
    session = relationship("CouncilSession", back_populates="decision")
```

**Indexes:**
- `idx_council_session_agent_status` - (agent_id, status)
- `idx_council_response_session` - (session_id)
- `idx_council_review_session` - (session_id)
- `idx_council_decision_session` - (session_id)

**CHECK Constraints:**
- status IN ('pending', 'reviewing', 'complete')
- decision_type IN ('architecture', 'planning', 'quality', 'generation')

#### 2. Alembic Migration (2h)

**File:** `backend/alembic/versions/012_add_llm_council_tables.py` (~150 lines)

**Tasks:**
- Create 4 tables with proper foreign keys
- Add indexes for performance
- Add CHECK constraints
- Test migration (upgrade + downgrade)
- Verify CASCADE DELETE behavior

**Migration Commands:**
```bash
# Generate migration
cd backend
alembic revision -m "add_llm_council_tables"

# Apply migration
alembic upgrade head

# Verify
docker exec project_manager_db psql -U user -d project_manager -c "\dt council_*"
```

#### 3. TypeScript Types (2h)

**File:** `backend/agents/types/LLMCouncil.ts` (~200 lines)

**Types to Define:**
- SessionStatus enum
- DecisionType enum
- CouncilSession interface
- CouncilResponse interface
- CouncilReview interface
- CouncilDecision interface
- CreateSessionRequest interface
- QuickDecisionRequest interface
- Helper functions (calculateConsensus, detectOutliers)

**Example:**
```typescript
export enum DecisionType {
    ARCHITECTURE = 'architecture',
    PLANNING = 'planning',
    QUALITY = 'quality',
    GENERATION = 'generation'
}

export interface CouncilSession {
    id: string;
    question: string;
    context: Record<string, any>;
    decision_type: DecisionType;
    agent_id: string;
    status: SessionStatus;
    created_at: Date;
    completed_at?: Date;
    responses?: CouncilResponse[];
    decision?: CouncilDecision;
}

export interface CouncilModelsConfig {
    chairman: {
        model: string;  // "deepseek-r1:latest"
        weight: number; // 2.0
        role: string;   // "chairman"
    };
    council: Array<{
        model: string;
        weight: number;
        role: string;
        specialty: string;
    }>;
}
```

### Day 1 Success Criteria
- [ ] 4 models created with relationships
- [ ] Migration 012 applied successfully
- [ ] TypeScript types complete
- [ ] Tables verified in PostgreSQL

---

## 🗓️ Day 2 (Tuesday): Core Service - Stage 1 Response (8h)

### Deliverables
- LLMCouncilService class
- Ollama integration (async concurrent)
- Stage 1: query_all_models()
- Session management

### Tasks

#### 1. LLM Council Service Foundation (3h)

**File:** `backend/app/services/llm_council_service.py` (~400 lines)

**Core Class:**
```python
class LLMCouncilService:
    """
    Multi-LLM consensus decision making service.

    3-Stage Process:
    1. Response: Query all models in parallel
    2. Peer Review: Models review each other (blind)
    3. Synthesis: Chairman creates final decision
    """

    def __init__(self, db_session: AsyncSession, ollama_base_url: str = "http://localhost:11434"):
        self.db = db_session
        self.ollama_url = ollama_base_url
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
        """Create new council session."""
        session = CouncilSession(
            id=uuid4(),
            question=question,
            context=context,
            decision_type=decision_type,
            agent_id=agent_id,
            status="pending",
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
```

**Methods to Implement:**
- `create_session()` - Initialize session
- `get_session()` - Retrieve with relationships
- `list_sessions()` - Filter by agent/status/type

#### 2. Ollama Integration (3h)

**Async Concurrent Calls:**
```python
async def query_all_models(
    self,
    session_id: UUID
) -> list[CouncilResponse]:
    """
    Stage 1: Query all models in parallel.

    Uses asyncio.gather for concurrent Ollama API calls.
    Each model receives same question + context.
    """
    # Get session
    session = await self.get_session(session_id)

    # Build prompt
    prompt = self._build_prompt(session.question, session.context, session.decision_type)

    # Query all models concurrently
    tasks = [
        self._query_single_model(model_name, prompt, session_id)
        for model_name in self.models.keys()
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failures, log errors
    successful_responses = [
        r for r in responses
        if isinstance(r, CouncilResponse)
    ]

    # Update session status
    if successful_responses:
        session.status = "reviewing"
        await self.db.commit()

    return successful_responses

async def _query_single_model(
    self,
    model_name: str,
    prompt: str,
    session_id: UUID
) -> CouncilResponse:
    """Query single Ollama model."""
    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                data = await response.json()

                # Parse response
                response_text = data.get("response", "")
                confidence = self._extract_confidence(response_text)
                reasoning = self._extract_reasoning(response_text)

                # Save to database
                council_response = CouncilResponse(
                    id=uuid4(),
                    session_id=session_id,
                    model_name=model_name,
                    response_text=response_text,
                    confidence=confidence,
                    reasoning=reasoning,
                    created_at=datetime.utcnow()
                )

                self.db.add(council_response)
                await self.db.commit()
                await self.db.refresh(council_response)

                return council_response

    except Exception as e:
        print(f"Error querying {model_name}: {e}")
        raise
```

#### 3. Prompt Engineering (2h)

**Decision Type Templates:**
```python
def _build_prompt(
    self,
    question: str,
    context: dict,
    decision_type: str
) -> str:
    """Build prompt based on decision type."""

    base_prompt = f"""
    You are participating in a technical council to make a critical decision.

    QUESTION:
    {question}

    CONTEXT:
    {self._format_context(context)}

    INSTRUCTIONS:
    1. Analyze the question carefully
    2. Consider the provided context
    3. Provide your recommendation
    4. Explain your reasoning
    5. Rate your confidence (0-100%)

    FORMAT YOUR RESPONSE AS:
    RECOMMENDATION: [Your specific recommendation]
    REASONING: [Why you recommend this]
    CONFIDENCE: [0-100]%
    """

    # Add decision-type specific guidance
    if decision_type == "architecture":
        base_prompt += """

        ARCHITECTURE CONSIDERATIONS:
        - Scalability (how will this handle growth?)
        - Maintainability (how easy to modify?)
        - Performance (latency/throughput impacts?)
        - Security (potential vulnerabilities?)
        - Cost (infrastructure/operational costs?)
        """
    elif decision_type == "quality":
        base_prompt += """

        QUALITY ASSESSMENT:
        - Risk level (what could go wrong?)
        - Mitigation strategies (how to reduce risk?)
        - Testing requirements (what must be verified?)
        - Rollback plan (how to undo if needed?)
        """
    # ... other types

    return base_prompt
```

### Day 2 Success Criteria
- [ ] LLMCouncilService class created
- [ ] Ollama integration working (concurrent calls)
- [ ] Stage 1 (query_all_models) functional
- [ ] Prompt engineering tested
- [ ] 6 models respond successfully

---

## 🗓️ Day 3 (Wednesday): Peer Review + Synthesis (8h)

### Deliverables
- Stage 2: peer_review()
- Stage 3: synthesize()
- Consensus calculation
- Outlier detection

### Tasks

#### 1. Peer Review Logic (4h)

**Stage 2 Implementation:**
```python
async def peer_review(
    self,
    session_id: UUID
) -> list[CouncilReview]:
    """
    Stage 2: Models review each other's responses (blind).

    Each model reviews all OTHER models' responses.
    Reviews are anonymous (model names hidden during review).
    """
    # Get session with responses
    session = await self.get_session(session_id)
    responses = session.responses

    if len(responses) < 2:
        raise ValueError("Need at least 2 responses for peer review")

    # Anonymize responses
    anonymized_responses = self._anonymize_responses(responses)

    # Each model reviews all others
    review_tasks = []
    for reviewer_model in self.models.keys():
        # Find this model's response
        reviewer_response = next(
            (r for r in responses if r.model_name == reviewer_model),
            None
        )

        if not reviewer_response:
            continue

        # Review all other responses
        for response_to_review in responses:
            if response_to_review.model_name == reviewer_model:
                continue  # Don't review own response

            review_tasks.append(
                self._review_single_response(
                    reviewer_model,
                    response_to_review,
                    session,
                    anonymized_responses
                )
            )

    # Execute all reviews concurrently
    reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

    # Filter successful reviews
    successful_reviews = [
        r for r in reviews
        if isinstance(r, CouncilReview)
    ]

    # Update session status
    if successful_reviews:
        session.status = "complete"  # Ready for synthesis
        await self.db.commit()

    return successful_reviews

async def _review_single_response(
    self,
    reviewer_model: str,
    response_to_review: CouncilResponse,
    session: CouncilSession,
    anonymized_map: dict
) -> CouncilReview:
    """Single model reviews another's response."""

    # Build review prompt
    prompt = f"""
    You are peer-reviewing a technical recommendation from another expert.

    ORIGINAL QUESTION:
    {session.question}

    RECOMMENDATION TO REVIEW:
    {response_to_review.response_text}

    Rate this recommendation on:
    1. ACCURACY (0-10): Is it technically correct?
    2. COMPLETENESS (0-10): Does it address all aspects?
    3. CLARITY (0-10): Is it easy to understand?
    4. FEASIBILITY (0-10): Can it be realistically implemented?

    Provide brief comments explaining your scores.

    FORMAT:
    ACCURACY: [0-10]
    COMPLETENESS: [0-10]
    CLARITY: [0-10]
    FEASIBILITY: [0-10]
    COMMENTS: [Your explanation]
    """

    try:
        # Query reviewer model
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": reviewer_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                data = await response.json()
                review_text = data.get("response", "")

                # Parse scores
                scores = self._parse_review_scores(review_text)

                # Save review
                review = CouncilReview(
                    id=uuid4(),
                    session_id=session.id,
                    reviewer_model=reviewer_model,
                    reviewed_response_id=response_to_review.id,
                    accuracy_score=scores["accuracy"],
                    completeness_score=scores["completeness"],
                    clarity_score=scores["clarity"],
                    feasibility_score=scores["feasibility"],
                    comments=scores.get("comments"),
                    created_at=datetime.utcnow()
                )

                self.db.add(review)
                await self.db.commit()
                await self.db.refresh(review)

                return review

    except Exception as e:
        print(f"Error in peer review by {reviewer_model}: {e}")
        raise
```

#### 2. Synthesis Logic (4h)

**Stage 3 Implementation:**
```python
async def synthesize(
    self,
    session_id: UUID,
    chairman_model: str = "deepseek-r1:latest"
) -> CouncilDecision:
    """
    Stage 3: Chairman synthesizes final decision.

    Considers:
    - All model responses
    - Peer review scores
    - Model weights
    - Consensus level
    """
    # Get session with responses and reviews
    session = await self.get_session(session_id)

    # Calculate aggregate scores per response
    response_scores = self._calculate_aggregate_scores(
        session.responses,
        session.reviews
    )

    # Calculate consensus level
    consensus_level = self._calculate_consensus(response_scores)

    # Identify outliers/dissenting opinions
    dissenting_opinions = self._detect_outliers(
        session.responses,
        response_scores
    )

    # Build synthesis prompt for chairman
    prompt = f"""
    You are the chairman synthesizing the council's decision.

    ORIGINAL QUESTION:
    {session.question}

    COUNCIL RESPONSES ({len(session.responses)}):
    {self._format_responses_for_synthesis(session.responses, response_scores)}

    PEER REVIEW SUMMARY:
    {self._format_review_summary(session.reviews)}

    CONSENSUS LEVEL: {consensus_level:.1f}%

    TASK:
    Synthesize the best elements from all responses into a final recommendation.
    Balance majority opinions with valuable dissenting views.
    Explain your reasoning and rate your confidence.

    FORMAT:
    FINAL DECISION: [Synthesized recommendation]
    REASONING: [Why this synthesis is best]
    CONFIDENCE: [0-100]%
    KEY CONSIDERATIONS: [Important points to remember]
    """

    # Query chairman model
    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": chairman_model,
                "prompt": prompt,
                "stream": False
            },
            timeout=aiohttp.ClientTimeout(total=90)  # Longer for synthesis
        ) as response:
            data = await response.json()
            decision_text = data.get("response", "")

            # Parse decision
            final_decision = self._extract_decision(decision_text)
            confidence = self._extract_confidence(decision_text)

            # Save decision
            decision = CouncilDecision(
                id=uuid4(),
                session_id=session.id,
                chairman_model=chairman_model,
                final_decision=final_decision,
                confidence=confidence,
                consensus_level=consensus_level,
                dissenting_opinions=dissenting_opinions,
                created_at=datetime.utcnow()
            )

            self.db.add(decision)

            # Update session
            session.completed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(decision)

            return decision

def _calculate_consensus(
    self,
    response_scores: dict
) -> float:
    """Calculate consensus level (0-100%)."""
    if not response_scores:
        return 0.0

    # Calculate variance in scores
    scores = list(response_scores.values())
    mean_score = statistics.mean(scores)
    variance = statistics.variance(scores) if len(scores) > 1 else 0

    # Lower variance = higher consensus
    # Normalize to 0-100 scale
    consensus = max(0, 100 - (variance * 10))

    return consensus

def _detect_outliers(
    self,
    responses: list,
    scores: dict
) -> list[str]:
    """Detect dissenting opinions (outliers)."""
    if len(scores) < 3:
        return []

    score_values = list(scores.values())
    mean = statistics.mean(score_values)
    stdev = statistics.stdev(score_values)

    outliers = []
    for response in responses:
        score = scores.get(response.id, 0)
        z_score = abs((score - mean) / stdev) if stdev > 0 else 0

        if z_score > 2:  # More than 2 standard deviations
            outliers.append(response.response_text[:200])  # First 200 chars

    return outliers
```

### Day 3 Success Criteria
- [ ] Stage 2 (peer_review) functional
- [ ] Stage 3 (synthesize) functional
- [ ] Consensus calculation working
- [ ] Outlier detection working
- [ ] Full 3-stage pipeline tested

---

## 🗓️ Day 4 (Thursday): REST API + Felix Integration (8h)

### Deliverables
- 8 REST API endpoints
- Pydantic schemas
- Felix agent integration
- Decision implementation hooks

### Tasks

#### 1. REST API Endpoints (4h)

**File:** `backend/app/api/llm_council.py` (~350 lines)

**8 Endpoints:**
```python
# POST /api/council/sessions - Create new session
# GET  /api/council/sessions - List sessions
# GET  /api/council/sessions/{id} - Get session details
# POST /api/council/sessions/{id}/query - Execute Stage 1 (query models)
# POST /api/council/sessions/{id}/review - Execute Stage 2 (peer review)
# POST /api/council/sessions/{id}/synthesize - Execute Stage 3 (synthesis)
# GET  /api/council/sessions/{id}/decision - Get final decision
# POST /api/council/quick - All 3 stages in one call (convenience)
```

**Pydantic Schemas:**
```python
class CreateSessionRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=5000)
    context: Dict = Field(default_factory=dict)
    decision_type: str = Field(..., pattern="^(architecture|planning|quality|generation)$")
    agent_id: str = Field(..., min_length=1, max_length=50)

class SessionResponse(BaseModel):
    id: str
    question: str
    context: Dict
    decision_type: str
    agent_id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    responses: Optional[List[ResponseSummary]]
    decision: Optional[DecisionSummary]

class QuickDecisionRequest(BaseModel):
    """All-in-one: create session + run 3 stages."""
    question: str
    context: Dict
    decision_type: str
    agent_id: str
    chairman_model: str = "deepseek-r1:latest"
```

**Router Registration:**
```python
# In main.py
from app.api import llm_council

app.include_router(llm_council.router)  # Week 52: LLM Council
```

#### 2. Felix Integration (4h)

**File:** `backend/agents/integrations/felix_council.ts` (~200 lines)

**Architecture Decision Hook:**
```typescript
import { LLMCouncilClient } from './llm_council_client';

export class FelixCouncilIntegration {
    private council: LLMCouncilClient;

    constructor(apiBaseUrl: string) {
        this.council = new LLMCouncilClient(apiBaseUrl);
    }

    async makeArchitectureDecision(
        question: string,
        context: {
            requirements: string[];
            constraints: string[];
            current_stack: string[];
        }
    ): Promise<ArchitectureDecision> {
        // Trigger council for critical architecture decision
        const session = await this.council.quickDecision({
            question: question,
            context: context,
            decision_type: "architecture",
            agent_id: "felix"
        });

        // Parse council decision
        const decision = {
            recommendation: session.decision.final_decision,
            confidence: session.decision.confidence,
            consensus_level: session.decision.consensus_level,
            dissenting_opinions: session.decision.dissenting_opinions,
            session_id: session.id
        };

        return decision;
    }

    shouldUseCouncil(complexity: number, impact: 'low' | 'medium' | 'high'): boolean {
        // Only use council for critical decisions
        if (impact === 'high') return true;
        if (impact === 'medium' && complexity > 7) return true;
        return false;
    }
}

// Usage in Felix
async function proposeArchitecture(task: Task): Promise<Architecture> {
    const complexity = calculateComplexity(task);
    const impact = assessImpact(task);

    if (felixCouncil.shouldUseCouncil(complexity, impact)) {
        // Use council for critical decision
        const councilDecision = await felixCouncil.makeArchitectureDecision(
            `What's the best architecture for: ${task.description}`,
            {
                requirements: task.requirements,
                constraints: task.constraints,
                current_stack: getCurrentStack()
            }
        );

        return implementArchitecture(councilDecision);
    } else {
        // Felix decides alone for simple cases
        return felixSoloDecision(task);
    }
}
```

### Day 4 Success Criteria
- [ ] 8 API endpoints working
- [ ] Pydantic validation complete
- [ ] Felix integration hooks created
- [ ] End-to-end test (Felix → Council → Decision)

---

## 🗓️ Day 5 (Friday): Testing + Dashboard + Documentation (8h)

### Deliverables
- 25+ comprehensive tests
- Council dashboard UI
- Documentation updates
- Performance benchmarks

### Tasks

#### 1. Testing (4h)

**Unit Tests** (`test_llm_council_service.py` - 12 tests):
```python
# Session management
- test_create_session()
- test_get_session_with_relationships()
- test_list_sessions_filtered()

# Stage 1: Response
- test_query_all_models_success()
- test_query_single_model_timeout()
- test_parallel_execution()

# Stage 2: Peer Review
- test_peer_review_anonymization()
- test_review_scoring()
- test_review_all_models()

# Stage 3: Synthesis
- test_consensus_calculation()
- test_outlier_detection()
- test_chairman_synthesis()
```

**Integration Tests** (`test_llm_council_api.py` - 10 tests):
```python
# API endpoints
- test_create_session_valid()
- test_create_session_invalid_type()
- test_execute_stage_1()
- test_execute_stage_2()
- test_execute_stage_3()
- test_quick_decision()
- test_get_decision()

# Error handling
- test_ollama_unavailable()
- test_insufficient_responses()
- test_concurrent_stage_execution()
```

**Agent Integration Tests** (`test_felix_council.py` - 5 tests):
```python
# Felix integration
- test_felix_architecture_decision()
- test_council_threshold_logic()
- test_decision_implementation()
- test_fallback_to_solo_decision()
- test_session_tracking()
```

#### 2. Dashboard UI (3h)

**File:** `frontend/llm-council-dashboard.html` (~400 lines)

**Features:**
- Council session list (filterable by agent, type, status)
- Session detail view
  - Question + context display
  - Response comparison table (6 models side-by-side)
  - Peer review matrix (model × model scores)
  - Consensus visualization (gauge chart)
  - Final decision with dissenting opinions
- Create new session form
- Quick decision shortcut

**Key Components:**
```html
<!-- Response Comparison Table -->
<table class="response-comparison">
    <thead>
        <tr>
            <th>Model</th>
            <th>Role</th>
            <th>Recommendation</th>
            <th>Confidence</th>
            <th>Avg Review Score</th>
        </tr>
    </thead>
    <tbody>
        <!-- 6 models × response data -->
    </tbody>
</table>

<!-- Consensus Gauge -->
<div class="consensus-gauge">
    <svg><!-- D3.js gauge chart --></svg>
    <div class="consensus-level">85% Consensus</div>
</div>

<!-- Decision Summary -->
<div class="decision-card">
    <h3>Final Decision</h3>
    <div class="decision-text">{{ final_decision }}</div>
    <div class="confidence">Confidence: {{ confidence }}%</div>
    <div class="dissenting" v-if="dissenting_opinions.length > 0">
        <h4>Dissenting Opinions:</h4>
        <ul>
            <li v-for="opinion in dissenting_opinions">{{ opinion }}</li>
        </ul>
    </div>
</div>
```

#### 3. Documentation (1h)

**Updates:**
- `ROADMAP.md` - Week 52 complete section
- `ARCHITECTURE.md` - LLM Council section
- `PROJECT_STATUS_SUMMARY.md` - Week 52 summary
- `LLM_COUNCIL_INTEGRATION.md` - Mark Week 51+52 complete

**New Documentation:**
- `docs/guides/LLM_COUNCIL_USAGE.md` - User guide
- `docs/api/llm_council_api_reference.md` - API docs

### Day 5 Success Criteria
- [ ] 25+ tests passing
- [ ] Dashboard UI functional
- [ ] Documentation updated
- [ ] Performance benchmarks recorded
- [ ] Week 52 COMPLETE

---

## 📊 Week 52 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Consensus Accuracy** | >80% | Decision quality vs actual outcome |
| **Response Time** | <30s | Full 3-stage cycle |
| **Model Availability** | 95%+ | Successful model responses |
| **Council Coverage** | 100% | All 6 models participate |
| **Agent Integration** | Felix complete | Architecture decisions via council |

---

## 🎯 Week 52 Expected Output

**Code Volume:**
- Production code: ~1,750 lines
- Test code: ~600 lines
- UI code: ~400 lines
- **Total: ~2,750 lines**

**Database:**
- 4 new tables (council_sessions, council_responses, council_reviews, council_decisions)
- 4 indexes
- 2 CHECK constraints
- Migration 012

**API:**
- 8 new endpoints
- 6 Pydantic schemas
- Full CRUD operations

**Services:**
- LLMCouncilService (~400 lines)
- Ollama integration (concurrent)
- 3-stage pipeline

**Agent Integration:**
- Felix architecture decisions
- Decision threshold logic
- Council trigger hooks

**Testing:**
- 12 unit tests
- 10 integration tests
- 5 agent integration tests
- Performance benchmarks

**UI:**
- Council dashboard (~400 lines)
- Session viewer
- Response comparison
- Consensus visualization

---

## 🚨 Risk Mitigation

### Risk 1: Ollama Model Availability
**Impact:** HIGH
**Mitigation:**
- Health checks before session creation
- Graceful degradation (min 4 models required)
- Retry logic with exponential backoff
- Fallback to agent solo decision

### Risk 2: Consensus Too Low
**Impact:** MEDIUM
**Mitigation:**
- Consensus threshold: 60% minimum
- Below threshold → surface dissenting opinions
- Human escalation option
- Log low-consensus sessions for review

### Risk 3: Performance (30s target)
**Impact:** MEDIUM
**Mitigation:**
- Parallel execution (asyncio.gather)
- Timeout per model: 60s
- Early termination if majority responds
- Cache chairman prompts

### Risk 4: Prompt Engineering Quality
**Impact:** HIGH
**Mitigation:**
- Decision-type specific prompts
- Iterative refinement (test with real questions)
- Response parsing robustness
- Manual review of first 10 sessions

---

## 🔄 Integration with Existing System

**Agents That Use Council:**
1. **Felix (Architecture)** - Week 52 Day 4 ✅
2. **Peter (Requirements)** - Week 53 (next week)
3. **Paul (Planning)** - Week 53 (next week)
4. **Quinn (Quality Gate Overrides)** - Week 53 (next week)

**When to Use Council:**
```typescript
const COUNCIL_THRESHOLDS = {
    architecture: { complexity: 7, impact: 'medium' },
    planning: { complexity: 8, impact: 'high' },
    quality: { override: true, severity: 'critical' },
    generation: { story_count: 10, uncertainty: 0.3 }
};

function shouldUseCouncil(task: Task, type: DecisionType): boolean {
    const threshold = COUNCIL_THRESHOLDS[type];
    const complexity = calculateComplexity(task);
    const impact = assessImpact(task);

    return (
        complexity >= threshold.complexity &&
        impact === threshold.impact
    );
}
```

---

## 📅 Week 52 → Week 53 Bridge

**Week 52 Deliverables:**
- ✅ LLM Council Foundation complete
- ✅ Felix integration working
- ✅ Dashboard UI operational

**Week 53 Goals:**
- Expand to Peter/Paul/Quinn
- Production validation (10+ real decisions)
- Performance tuning
- Monitoring & alerting

---

## 🎉 Week 52 Definition of Done

- [ ] Database: 4 tables created, migration 012 applied
- [ ] Service: LLMCouncilService with 3-stage pipeline
- [ ] API: 8 endpoints operational
- [ ] Felix: Architecture decisions via council
- [ ] Testing: 25+ tests passing (>90% coverage)
- [ ] Dashboard: Council UI functional
- [ ] Documentation: All docs updated
- [ ] Performance: <30s full cycle
- [ ] Ollama: 6 models available (>95% uptime)
- [ ] Integration: End-to-end Felix → Council → Decision

---

**Created:** 2025-11-25
**Author:** Eddie + Claude Code
**Status:** READY FOR IMPLEMENTATION 🚀
**Estimated Completion:** 2025-12-06 (Friday Week 52)
