# LLM Council Improvements Plan

**Document:** Architecture Decision Record
**Status:** PLANNED
**Created:** Week 144 (2026-01-09)
**Priority:** LOW (niet urgent)
**Roadmap:** Fase 30 (Week 233+)
**Origin:** Analyse van externe repos (sage2, llm-council, lm-council, llm-council-plus)

---

## Executive Summary

Dit document beschrijft verbeteringen aan de bestaande LLM Council implementatie, gebaseerd op analyse van 4 externe repositories. De huidige implementatie is functioneel compleet; deze verbeteringen zijn optimalisaties, geen kritieke features.

**Huidige Implementatie:**
- 3-stage process (Response → Peer Review → Synthesis)
- 6 Ollama modellen met gewichten
- Consensus berekening met standard deviation
- PostgreSQL persistentie met volledige audit trail
- Chairman synthesis voor finale beslissing

**Voorgestelde Verbeteringen:**
1. SSE Streaming (real-time response visibility)
2. Stage-Level Timeouts (graceful degradation)
3. Model Performance Tracking (data-driven weights)
4. Web Search Context Enrichment (actuele informatie)

---

## Analyse Bronnen

| Repository | URL | Relevante Features |
|------------|-----|-------------------|
| **sage2** | github.com/zeeneddie/sage2 | SSE streaming, performance tracking |
| **llm-council** | github.com/zeeneddie/llm-council | Model weights, consensus algorithms |
| **lm-council** | github.com/zeeneddie/lm-council | Timeouts, retry logic |
| **llm-council-plus** | github.com/zeeneddie/llm-council-plus | Web search integration |

---

## Verbetering 1: SSE Streaming (Server-Sent Events)

### WAT

Real-time streaming van LLM responses naar de client via Server-Sent Events. In plaats van te wachten tot alle 6 modellen klaar zijn, krijgt de gebruiker direct de eerste tokens te zien zodra elk model begint te antwoorden.

### WAAROM

**Huidige situatie:**
De council draait 6 modellen sequentieel/parallel, maar de gebruiker ziet NIETS totdat alle responses binnen zijn. Bij grote analyses kan dit 30-60 seconden stilte zijn.

**Probleem:**
Gebruikers denken dat het systeem vastloopt, sluiten de pagina, of verliezen vertrouwen.

### WAARDE

| Aspect | Impact |
|--------|--------|
| **UX Perceived Performance** | 10x beter gevoel - gebruiker ziet direct activiteit |
| **Transparantie** | Gebruiker ziet welk model wanneer antwoordt |
| **Debugging** | Direct zichtbaar als een model vastzit |
| **Vertrouwen** | "Het systeem denkt na" ipv "Is het stuk?" |

### Technische Implementatie

```python
# backend/app/services/llm_council_streaming_service.py

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

class CouncilStreamingService:
    """SSE streaming voor LLM Council responses."""

    async def stream_council_session(
        self,
        session_id: str,
        prompt: str
    ) -> AsyncGenerator[dict, None]:
        """
        Stream council responses in real-time.

        Events:
        - stage_start: {stage: "response"|"review"|"synthesis", model: str}
        - token: {model: str, token: str, stage: str}
        - stage_complete: {stage: str, model: str, result: str}
        - council_complete: {decision: str, consensus_score: float}
        """
        # Stage 1: Initial Responses
        yield {"event": "stage_start", "data": {"stage": "response"}}

        async for model_name, token in self._stream_model_responses(prompt):
            yield {
                "event": "token",
                "data": {"model": model_name, "token": token, "stage": "response"}
            }

        # Stage 2: Peer Reviews
        yield {"event": "stage_start", "data": {"stage": "review"}}

        # ... streaming peer reviews

        # Stage 3: Chairman Synthesis
        yield {"event": "stage_start", "data": {"stage": "synthesis"}}

        # ... streaming synthesis

        yield {
            "event": "council_complete",
            "data": {"decision": final_decision, "consensus_score": score}
        }


@router.get("/council/{session_id}/stream")
async def stream_council_response(session_id: str, prompt: str):
    """SSE endpoint voor real-time council streaming."""
    service = CouncilStreamingService()

    async def event_generator():
        async for event in service.stream_council_session(session_id, prompt):
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"])
            }

    return EventSourceResponse(event_generator())
```

### Frontend Integratie

```javascript
// frontend/js/council-streaming.js

class CouncilStreamViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.modelCards = {};
    }

    connect(sessionId, prompt) {
        const url = `/api/council/${sessionId}/stream?prompt=${encodeURIComponent(prompt)}`;
        this.eventSource = new EventSource(url);

        this.eventSource.addEventListener('stage_start', (e) => {
            const data = JSON.parse(e.data);
            this.showStageIndicator(data.stage);
        });

        this.eventSource.addEventListener('token', (e) => {
            const data = JSON.parse(e.data);
            this.appendToken(data.model, data.token);
        });

        this.eventSource.addEventListener('council_complete', (e) => {
            const data = JSON.parse(e.data);
            this.showFinalDecision(data);
        });
    }

    appendToken(model, token) {
        if (!this.modelCards[model]) {
            this.modelCards[model] = this.createModelCard(model);
        }
        this.modelCards[model].querySelector('.response').textContent += token;
    }
}
```

### Effort & ROI

| Metric | Value |
|--------|-------|
| **Implementation Effort** | 2-3 dagen |
| **Test Coverage** | 20+ tests |
| **UX Impact** | HIGH - 10x betere perceived performance |
| **Complexity** | MEDIUM - requires SSE infrastructure |

---

## Verbetering 2: Stage-Level Timeouts

### WAT

Individuele timeouts per council stage (Response → Review → Synthesis) in plaats van één globale timeout. Elke fase krijgt een eigen tijdslimiet met graceful degradation.

### WAAROM

**Huidige situatie:**
Als één model in de Review-fase vastloopt, wacht het systeem de volledige timeout af.

**Probleem:**
Een trage `deepseek-r1` in Phase 2 blokkeert de hele council 60+ seconden.

### WAARDE

| Aspect | Impact |
|--------|--------|
| **Reliability** | Systeem blijft werken ook als 1 model faalt |
| **Response Time** | 40-60% sneller in edge cases (één model traag) |
| **Resource Efficiency** | Geen verspilde compute op vastgelopen requests |
| **Graceful Degradation** | Council geeft resultaat met 5/6 modellen ipv error |

### Technische Implementatie

```python
# backend/app/services/llm_council_service.py (enhanced)

from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass
class StageTimeoutConfig:
    """Timeout configuratie per council stage."""
    response_timeout: int = 30      # Max 30s voor initial response per model
    review_timeout: int = 20        # Max 20s voor peer review per model
    synthesis_timeout: int = 15     # Max 15s voor chairman synthesis

    # Graceful degradation settings
    min_responses_required: int = 4  # Minimaal 4/6 modellen voor valid council
    min_reviews_required: int = 3    # Minimaal 3 reviews per response


class TimeoutAwareCouncilService:
    """LLM Council met stage-level timeouts en graceful degradation."""

    def __init__(self, config: StageTimeoutConfig = None):
        self.config = config or StageTimeoutConfig()
        self.timeout_stats = {}

    async def run_stage_with_timeout(
        self,
        stage: str,
        coroutines: list,
        timeout: int,
        min_required: int
    ) -> tuple[list, list[str]]:
        """
        Run stage met timeout en graceful degradation.

        Returns:
            (succesful_results, timed_out_models)
        """
        results = []
        timed_out = []

        # Gather met individuele timeouts
        tasks = [
            asyncio.wait_for(coro, timeout=timeout)
            for coro in coroutines
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(completed):
            if isinstance(result, asyncio.TimeoutError):
                timed_out.append(self.models[i].name)
                self._record_timeout(self.models[i].name, stage)
            elif isinstance(result, Exception):
                logger.error(f"Model {self.models[i].name} failed: {result}")
                timed_out.append(self.models[i].name)
            else:
                results.append(result)

        # Check minimum requirements
        if len(results) < min_required:
            raise InsufficientResponsesError(
                f"Stage {stage}: Got {len(results)} responses, need {min_required}"
            )

        return results, timed_out

    async def run_council_with_timeouts(
        self,
        session_id: str,
        prompt: str
    ) -> CouncilDecision:
        """Run full council met stage-level timeouts."""

        # Stage 1: Initial Responses
        response_coros = [
            self._get_model_response(model, prompt)
            for model in self.models
        ]
        responses, response_timeouts = await self.run_stage_with_timeout(
            stage="response",
            coroutines=response_coros,
            timeout=self.config.response_timeout,
            min_required=self.config.min_responses_required
        )

        # Stage 2: Peer Reviews (only for models that responded)
        responding_models = [m for m in self.models if m.name not in response_timeouts]
        review_coros = [
            self._get_peer_review(model, responses)
            for model in responding_models
        ]
        reviews, review_timeouts = await self.run_stage_with_timeout(
            stage="review",
            coroutines=review_coros,
            timeout=self.config.review_timeout,
            min_required=self.config.min_reviews_required
        )

        # Stage 3: Chairman Synthesis
        synthesis_coro = self._synthesize_decision(responses, reviews)
        try:
            decision = await asyncio.wait_for(
                synthesis_coro,
                timeout=self.config.synthesis_timeout
            )
        except asyncio.TimeoutError:
            # Fallback: use weighted average of responses
            decision = self._fallback_synthesis(responses, reviews)
            decision.metadata["synthesis_fallback"] = True

        # Record timeout statistics
        decision.metadata["timeouts"] = {
            "response": response_timeouts,
            "review": review_timeouts
        }

        return decision

    def _record_timeout(self, model_name: str, stage: str):
        """Record timeout voor performance tracking."""
        key = f"{model_name}:{stage}"
        self.timeout_stats[key] = self.timeout_stats.get(key, 0) + 1
```

### Configuration

```python
# backend/app/core/config.py

class CouncilSettings(BaseSettings):
    """LLM Council configuratie."""

    # Stage timeouts (seconds)
    COUNCIL_RESPONSE_TIMEOUT: int = 30
    COUNCIL_REVIEW_TIMEOUT: int = 20
    COUNCIL_SYNTHESIS_TIMEOUT: int = 15

    # Graceful degradation
    COUNCIL_MIN_RESPONSES: int = 4
    COUNCIL_MIN_REVIEWS: int = 3

    # Retry settings
    COUNCIL_MAX_RETRIES: int = 2
    COUNCIL_RETRY_DELAY: float = 1.0
```

### Effort & ROI

| Metric | Value |
|--------|-------|
| **Implementation Effort** | 1-2 dagen |
| **Test Coverage** | 15+ tests |
| **Reliability Impact** | HIGH - 40-60% sneller in edge cases |
| **Complexity** | LOW - straightforward async patterns |

---

## Verbetering 3: Model Performance Tracking / Leaderboard

### WAT

Automatisch bijhouden van model performance metrics: response time, consensus alignment, dissent frequency, en quality scores. Dashboard met leaderboard per use case.

### WAAROM

**Huidige situatie:**
Statische weights (`deepseek-r1: 2.0`, `qwen2.5: 1.5`) zonder data om deze te valideren.

**Probleem:**
Misschien is `codellama` beter voor code-analyse dan `deepseek-r1`, maar je weet het niet.

### WAARDE

| Aspect | Impact |
|--------|--------|
| **Data-Driven Weights** | Weights gebaseerd op echte performance, niet aannames |
| **Model Selection** | Automatisch beste model kiezen per task type |
| **Cost Optimization** | Identificeer welke modellen weinig toevoegen |
| **Quality Improvement** | Continue verbetering van council decisions |

### Technische Implementatie

```python
# backend/app/models/llm_council_performance.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.db.base_class import Base

class ModelPerformanceMetric(Base):
    """Per-model performance metrics."""
    __tablename__ = "model_performance_metrics"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False, index=True)

    # Timing metrics
    avg_response_time_ms = Column(Float, default=0.0)
    p95_response_time_ms = Column(Float, default=0.0)
    timeout_rate = Column(Float, default=0.0)

    # Quality metrics
    consensus_alignment_rate = Column(Float, default=0.0)  # Hoe vaak in lijn met final decision
    dissent_rate = Column(Float, default=0.0)              # Hoe vaak afwijkend
    peer_review_score_given = Column(Float, default=0.0)   # Gemiddelde score die dit model geeft
    peer_review_score_received = Column(Float, default=0.0) # Gemiddelde score die dit model krijgt

    # Use case performance (JSONB)
    use_case_scores = Column(JSON, default={})  # {"code_analysis": 0.85, "estimation": 0.72}

    # Aggregation
    total_sessions = Column(Integer, default=0)
    last_updated = Column(DateTime)

    # Calculated recommended weight
    recommended_weight = Column(Float, default=1.0)


class ModelLeaderboard(Base):
    """Leaderboard per use case."""
    __tablename__ = "model_leaderboard"

    id = Column(Integer, primary_key=True)
    use_case = Column(String(100), nullable=False, index=True)  # code_analysis, estimation, etc.

    # Rankings (JSONB array)
    rankings = Column(JSON, default=[])  # [{"model": "deepseek-r1", "score": 0.92, "rank": 1}, ...]

    # Statistics
    total_evaluations = Column(Integer, default=0)
    last_updated = Column(DateTime)
```

```python
# backend/app/services/model_performance_service.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import statistics

@dataclass
class PerformanceSnapshot:
    """Snapshot van model performance voor een sessie."""
    model_name: str
    response_time_ms: float
    aligned_with_consensus: bool
    peer_review_score: float
    use_case: str
    timestamp: datetime


class ModelPerformanceService:
    """Service voor het tracken en analyseren van model performance."""

    def __init__(self, db_session):
        self.db = db_session

    async def record_session_performance(
        self,
        session_id: str,
        snapshots: List[PerformanceSnapshot]
    ):
        """Record performance metrics van een council sessie."""
        for snapshot in snapshots:
            await self._update_model_metrics(snapshot)

        # Update leaderboard
        use_cases = set(s.use_case for s in snapshots)
        for use_case in use_cases:
            await self._update_leaderboard(use_case)

    async def _update_model_metrics(self, snapshot: PerformanceSnapshot):
        """Update incrementele metrics voor een model."""
        metrics = await self.db.query(ModelPerformanceMetric).filter(
            ModelPerformanceMetric.model_name == snapshot.model_name
        ).first()

        if not metrics:
            metrics = ModelPerformanceMetric(model_name=snapshot.model_name)
            self.db.add(metrics)

        # Exponential moving average voor response time
        alpha = 0.1  # Learning rate
        metrics.avg_response_time_ms = (
            alpha * snapshot.response_time_ms +
            (1 - alpha) * metrics.avg_response_time_ms
        )

        # Update consensus alignment
        metrics.total_sessions += 1
        current_alignment = 1.0 if snapshot.aligned_with_consensus else 0.0
        metrics.consensus_alignment_rate = (
            (metrics.consensus_alignment_rate * (metrics.total_sessions - 1) + current_alignment)
            / metrics.total_sessions
        )

        # Update use case scores
        if snapshot.use_case not in metrics.use_case_scores:
            metrics.use_case_scores[snapshot.use_case] = []
        metrics.use_case_scores[snapshot.use_case].append(snapshot.peer_review_score)

        # Recalculate recommended weight
        metrics.recommended_weight = self._calculate_recommended_weight(metrics)
        metrics.last_updated = datetime.utcnow()

        await self.db.commit()

    def _calculate_recommended_weight(self, metrics: ModelPerformanceMetric) -> float:
        """
        Bereken aanbevolen weight op basis van performance.

        Formula:
        weight = (alignment_score * 0.4) + (speed_score * 0.2) + (peer_score * 0.4)

        Normalized to range [0.5, 2.5]
        """
        # Alignment score (higher is better)
        alignment_score = metrics.consensus_alignment_rate

        # Speed score (lower response time = higher score)
        # Normalize: 0-1000ms = 1.0, 1000-3000ms = 0.5, >3000ms = 0.2
        if metrics.avg_response_time_ms < 1000:
            speed_score = 1.0
        elif metrics.avg_response_time_ms < 3000:
            speed_score = 0.5
        else:
            speed_score = 0.2

        # Peer review score (average score received)
        peer_score = metrics.peer_review_score_received / 10.0  # Normalize to 0-1

        # Weighted combination
        raw_weight = (alignment_score * 0.4) + (speed_score * 0.2) + (peer_score * 0.4)

        # Scale to [0.5, 2.5]
        return 0.5 + (raw_weight * 2.0)

    async def get_leaderboard(self, use_case: str) -> List[Dict]:
        """Get model rankings voor een specifieke use case."""
        leaderboard = await self.db.query(ModelLeaderboard).filter(
            ModelLeaderboard.use_case == use_case
        ).first()

        return leaderboard.rankings if leaderboard else []

    async def get_recommended_weights(self) -> Dict[str, float]:
        """Get recommended weights voor alle modellen."""
        metrics = await self.db.query(ModelPerformanceMetric).all()
        return {m.model_name: m.recommended_weight for m in metrics}
```

### Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM COUNCIL PERFORMANCE DASHBOARD                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OVERALL RANKINGS (Last 30 days)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  #1  deepseek-r1:latest      ████████████████████  92.3%  (2.3 wt)  │   │
│  │  #2  qwen2.5-coder:7b        ████████████████░░░░  85.7%  (1.8 wt)  │   │
│  │  #3  codellama:7b            ██████████████░░░░░░  78.2%  (1.5 wt)  │   │
│  │  #4  mistral:7b              █████████████░░░░░░░  72.1%  (1.3 wt)  │   │
│  │  #5  llama3.2:3b             ████████████░░░░░░░░  68.5%  (1.1 wt)  │   │
│  │  #6  gemma2:2b               ██████████░░░░░░░░░░  61.2%  (0.8 wt)  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  USE CASE BREAKDOWN                                                         │
│  ┌───────────────────┬───────────────────┬───────────────────┐             │
│  │ CODE ANALYSIS     │ ESTIMATION        │ DOCUMENTATION     │             │
│  │                   │                   │                   │             │
│  │ #1 qwen2.5-coder  │ #1 deepseek-r1    │ #1 mistral       │             │
│  │ #2 codellama      │ #2 qwen2.5        │ #2 deepseek-r1   │             │
│  │ #3 deepseek-r1    │ #3 mistral        │ #3 qwen2.5       │             │
│  └───────────────────┴───────────────────┴───────────────────┘             │
│                                                                             │
│  RESPONSE TIME (p95)                                                        │
│  deepseek-r1:  ████████████████████░░░░░  2.8s                             │
│  qwen2.5:      ████████████░░░░░░░░░░░░░  1.5s                             │
│  codellama:    ██████████░░░░░░░░░░░░░░░  1.2s                             │
│  mistral:      ████████░░░░░░░░░░░░░░░░░  0.9s                             │
│                                                                             │
│  TIMEOUT RATE (Last 7 days)                                                 │
│  deepseek-r1: 3.2%  |  qwen2.5: 1.1%  |  codellama: 0.8%  |  mistral: 0.5% │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Effort & ROI

| Metric | Value |
|--------|-------|
| **Implementation Effort** | 3-4 dagen (inclusief dashboard) |
| **Test Coverage** | 25+ tests |
| **Quality Impact** | MEDIUM - data-driven decision making |
| **Complexity** | MEDIUM - requires metrics infrastructure |

### Business Value

Na 100+ council sessions kun je statements maken zoals:
- "Voor code-analyse is `qwen2.5-coder` 23% beter dan `deepseek-r1`"
- "Model X voegt weinig toe aan consensus, overweeg verwijdering"
- "Response time van deepseek is 2x hoger maar accuracy is 15% beter"

---

## Verbetering 4: Web Search Context Enrichment

### WAT

Optionele web search integratie vóór de council deliberation. Haalt actuele informatie op voor context-afhankelijke vragen.

### WAAROM

**Huidige situatie:**
Council baseert zich alleen op model training data (cutoff ~2023-2024)

**Probleem:**
Vragen over recente frameworks, libraries, of best practices geven outdated antwoorden

### WAARDE

| Aspect | Impact |
|--------|--------|
| **Accuracy** | Actuele informatie voor tech-vragen |
| **Relevance** | Antwoorden gebaseerd op huidige documentatie |
| **Competitive Edge** | Combinatie van web search + multi-model consensus is zeldzaam |

### Wanneer Gebruiken

| Scenario | Web Search? | Reden |
|----------|-------------|-------|
| **Technology recommendations** | JA | Actuele versies, deprecations |
| **Security vulnerability checks** | JA | Recent CVEs |
| **Framework best practices** | JA | Docs kunnen wijzigen |
| **Code analysis** | NEE | Interne code |
| **Architecture decisions** | NEE | Principes wijzigen niet snel |
| **Estimation (FP/SP)** | NEE | Methodologie is stabiel |

### Technische Implementatie

```python
# backend/app/services/council_context_enrichment_service.py

from typing import Optional, List
from dataclasses import dataclass

@dataclass
class WebSearchResult:
    """Resultaat van web search."""
    query: str
    snippets: List[str]
    sources: List[str]
    timestamp: datetime


@dataclass
class EnrichedContext:
    """Verrijkte context voor council prompt."""
    original_prompt: str
    web_context: Optional[str]
    web_sources: List[str]
    enrichment_applied: bool


class CouncilContextEnrichmentService:
    """Service voor context enrichment via web search."""

    def __init__(self, web_search_client):
        self.web_search = web_search_client

        # Prompt types die baat hebben bij web search
        self.enrichable_types = {
            "technology_recommendation",
            "framework_comparison",
            "security_assessment",
            "best_practices_query",
            "version_compatibility"
        }

    async def should_enrich(self, prompt: str, prompt_type: str) -> bool:
        """Bepaal of prompt verrijkt moet worden met web search."""
        if prompt_type not in self.enrichable_types:
            return False

        # Check voor indicators die web search nuttig maken
        indicators = [
            "latest", "recent", "current", "2025", "2026",
            "best practice", "recommended", "should I use",
            "comparison", "vs", "versus", "alternative"
        ]

        return any(ind in prompt.lower() for ind in indicators)

    async def enrich_context(
        self,
        prompt: str,
        prompt_type: str,
        max_snippets: int = 5
    ) -> EnrichedContext:
        """Verrijk prompt met web search resultaten."""

        if not await self.should_enrich(prompt, prompt_type):
            return EnrichedContext(
                original_prompt=prompt,
                web_context=None,
                web_sources=[],
                enrichment_applied=False
            )

        # Extract search query from prompt
        search_query = await self._extract_search_query(prompt)

        # Perform web search
        results = await self.web_search.search(
            query=search_query,
            max_results=max_snippets
        )

        # Format as context
        web_context = self._format_web_context(results)

        return EnrichedContext(
            original_prompt=prompt,
            web_context=web_context,
            web_sources=[r.source for r in results.snippets],
            enrichment_applied=True
        )

    def _format_web_context(self, results: WebSearchResult) -> str:
        """Format web search results als context voor council."""
        if not results.snippets:
            return ""

        context_parts = [
            "## Recent Web Context (retrieved " +
            results.timestamp.strftime("%Y-%m-%d") + ")",
            ""
        ]

        for i, snippet in enumerate(results.snippets, 1):
            context_parts.append(f"**Source {i}:** {results.sources[i-1]}")
            context_parts.append(snippet)
            context_parts.append("")

        return "\n".join(context_parts)

    async def _extract_search_query(self, prompt: str) -> str:
        """Extract optimale search query uit prompt."""
        # Simple extraction: use key terms
        # In production: use LLM for query extraction

        # Remove common words
        stop_words = {"what", "how", "should", "can", "the", "a", "an", "is", "are"}
        words = prompt.lower().split()
        key_words = [w for w in words if w not in stop_words][:10]

        return " ".join(key_words)
```

### Integration met Council

```python
# backend/app/services/llm_council_service.py (enhanced)

class LLMCouncilService:

    def __init__(self, ...):
        self.context_enrichment = CouncilContextEnrichmentService(web_search_client)

    async def run_council(
        self,
        session_id: str,
        prompt: str,
        prompt_type: str = "general",
        enable_web_enrichment: bool = True
    ) -> CouncilDecision:
        """Run council met optionele web enrichment."""

        # Step 0: Context Enrichment (optional)
        if enable_web_enrichment:
            enriched = await self.context_enrichment.enrich_context(
                prompt=prompt,
                prompt_type=prompt_type
            )

            if enriched.enrichment_applied:
                prompt = f"""
{enriched.web_context}

---

## Original Question
{enriched.original_prompt}

Please consider the recent web context above when formulating your response.
"""

        # Step 1-3: Normal council flow
        # ...

        # Add enrichment metadata to decision
        decision.metadata["web_enrichment"] = {
            "applied": enriched.enrichment_applied if enable_web_enrichment else False,
            "sources": enriched.web_sources if enable_web_enrichment else []
        }

        return decision
```

### Effort & ROI

| Metric | Value |
|--------|-------|
| **Implementation Effort** | 2 dagen (met bestaande web search) |
| **Test Coverage** | 15+ tests |
| **Accuracy Impact** | MEDIUM - 20% improvement voor specifieke cases |
| **Complexity** | LOW - builds on existing infrastructure |

---

## Implementation Phases

### Phase 1: SSE Streaming (Week 233)

| Task | Hours | Deliverable |
|------|-------|-------------|
| SSE infrastructure setup | 4 | `sse_starlette` integration |
| `CouncilStreamingService` | 6 | Streaming service |
| Frontend stream viewer | 4 | JavaScript SSE client |
| Unit tests | 4 | 20+ tests |
| Integration tests | 2 | E2E streaming test |
| **Total** | **20** | |

### Phase 2: Stage Timeouts (Week 233-234)

| Task | Hours | Deliverable |
|------|-------|-------------|
| `TimeoutAwareCouncilService` | 4 | Timeout-aware service |
| Configuration system | 2 | Stage timeout config |
| Graceful degradation logic | 4 | Fallback synthesis |
| Unit tests | 4 | 15+ tests |
| **Total** | **14** | |

### Phase 3: Performance Tracking (Week 234)

| Task | Hours | Deliverable |
|------|-------|-------------|
| Database schema | 2 | Performance tables |
| `ModelPerformanceService` | 6 | Tracking service |
| Weight calculation algorithm | 4 | Recommended weights |
| Leaderboard API | 4 | REST endpoints |
| Dashboard | 6 | Performance dashboard |
| Unit tests | 4 | 25+ tests |
| **Total** | **26** | |

### Phase 4: Web Enrichment (Week 235)

| Task | Hours | Deliverable |
|------|-------|-------------|
| `CouncilContextEnrichmentService` | 4 | Enrichment service |
| Query extraction | 2 | Search query generator |
| Council integration | 2 | Modified council flow |
| Unit tests | 4 | 15+ tests |
| **Total** | **12** | |

---

## Total Effort Summary

| Phase | Effort | Duration |
|-------|--------|----------|
| SSE Streaming | 20 uur | 2-3 dagen |
| Stage Timeouts | 14 uur | 1-2 dagen |
| Performance Tracking | 26 uur | 3-4 dagen |
| Web Enrichment | 12 uur | 2 dagen |
| **Total** | **72 uur** | **~2 weken** |

---

## API Endpoints (New)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/council/{session_id}/stream` | GET | SSE streaming endpoint |
| `/api/council/performance/metrics` | GET | Get all model metrics |
| `/api/council/performance/leaderboard/{use_case}` | GET | Get leaderboard |
| `/api/council/performance/weights/recommended` | GET | Get recommended weights |
| `/api/council/config/timeouts` | GET/PUT | Get/update timeout config |

---

## Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Perceived response time | 30-60s waiting | <5s first token | 10x better UX |
| Edge case latency | 60s+ (timeout) | <30s (graceful) | 50% faster |
| Weight accuracy | Static (assumed) | Data-driven | Measurable |
| Info currency | Training cutoff | Real-time | Current data |

---

## Niet Over Te Nemen

| Feature | Bron | Reden |
|---------|------|-------|
| Sage2 full framework | sage2 | Overkill - werkende council exists |
| CLI-only interface | lm-council | Geen web interface, niet relevant |
| Excessive abstraction | llm-council-plus | Te veel complexity voor weinig winst |
| Custom model hosting | diverse | Ollama werkt prima |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| SSE library (`sse-starlette`) | TO INSTALL | pip install sse-starlette |
| Web search service | EXISTS | Existing infrastructure |
| Ollama | EXISTS | 6 models configured |
| PostgreSQL | EXISTS | Database ready |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [llm_council_service.py](../../backend/app/services/llm_council_service.py) | Current implementation |
| [llm_council.py](../../backend/app/models/llm_council.py) | Data models |
| [phases-planned.md](../roadmap/phases-planned.md) | Roadmap (Fase 30) |

---

*Generated: Week 144 (2026-01-09)*
