# Fase 24.5: LLM Resilience & Streaming

**Project:** MarQed AI Agent Software Platform
**Week:** 159-160
**Duration:** 3-4 dagen
**Priority:** 🟠 HIGH (voorkomt ~10% failed analyses)
**ROI:** 7.5
**Author:** Claude Code (Week 158)
**Created:** 2026-01-19

---

## Executive Summary

Deze fase adresseert twee kritieke gaps in de huidige LLM integratie:

1. **Geen Retry Logic** - Een enkele timeout of 503 error resulteert in complete failure
2. **Geen Streaming** - Gebruikers wachten 30-60 seconden zonder feedback

**Impact na implementatie:**
- Failed analyses: ~13% → <3%
- Perceived latency: 30-60s → <5s (first token)
- User experience: Significant verbeterd

---

## Problem Analysis

### Problem 1: No Retry Logic

**Current State** (`extraction_llm_adapter.py:415-496`):

```python
async def call_ollama(self, model, prompt, ...):
    try:
        async with session.post(...) as resp:
            if resp.status != 200:
                return LLMCallResult(success=False, error="...")  # ❌ IMMEDIATE FAIL
    except asyncio.TimeoutError:
        return LLMCallResult(success=False, error="Timeout")      # ❌ NO RETRY
    except Exception as e:
        return LLMCallResult(success=False, error=str(e))         # ❌ NO RETRY
```

**Failure Scenarios:**

| Error Type | HTTP Code | Frequency | Retryable? | Current Handling |
|------------|-----------|-----------|------------|------------------|
| Rate Limited | 429 | 10-20% peak | ✅ Yes | ❌ Immediate fail |
| Server Overload | 503 | 5-10% | ✅ Yes | ❌ Immediate fail |
| Gateway Timeout | 504 | 2-5% | ✅ Yes | ❌ Immediate fail |
| Network Timeout | - | 2-5% | ✅ Yes | ❌ Immediate fail |
| Bad Request | 400 | 1-2% | ❌ No | ✅ Correct (fail) |
| Auth Error | 401/403 | <1% | ❌ No | ✅ Correct (fail) |

**Business Impact:**
- ~13% van analyses faalt door retryable errors
- Gebruikers moeten handmatig opnieuw starten
- Kosten: verspilde compute + gefrustreerde gebruikers

### Problem 2: No Streaming Support

**Current State** (`extraction_llm_adapter.py:431`):

```python
payload = {
    "model": model,
    "prompt": prompt,
    "stream": False,  # ❌ WAIT FOR COMPLETE RESPONSE
}
```

**User Experience Impact:**

| Response Size | Generation Time | Current UX | With Streaming |
|---------------|-----------------|------------|----------------|
| 500 tokens | ~5s | ⏳ 5s blank | ✅ Instant start |
| 2000 tokens | ~15s | ⏳ 15s blank | ✅ Progressive |
| 5000 tokens | ~45s | ⏳ 45s blank | ✅ Progressive |
| Timeout (60s) | 60s+ | ❌ 0 output | ✅ Partial output |

**Technical Limitations:**
- Ollama supports streaming natively (`stream: true`)
- Claude CLI supports `--stream` flag
- Current implementation explicitly disables both

---

## Solution Design

### Component 1: Retry Logic with Exponential Backoff

**Pattern:** Exponential backoff with jitter

```
Attempt 1: Immediate
Attempt 2: Wait 1s + jitter (0-0.1s)
Attempt 3: Wait 2s + jitter (0-0.2s)
Attempt 4: Wait 4s + jitter (0-0.4s)
Max delay: 30s
```

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    LLMCallWithRetry                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ RetryPolicy │───▶│ call_func() │───▶│ LLMResult   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ max_retries │    │ is_retry-   │    │ success?    │     │
│  │ base_delay  │    │ able_error? │    │   → return  │     │
│  │ max_delay   │    │   → retry   │    │   → retry?  │     │
│  │ jitter      │    │   → fail    │    └─────────────┘     │
│  └─────────────┘    └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Retry Policy Configuration:**

```python
@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter_factor: float = 0.1
    retryable_status_codes: Set[int] = field(default_factory=lambda: {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    })
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        asyncio.TimeoutError,
        aiohttp.ClientError,
        ConnectionError,
    )
```

**Tier-Based Retry Policies:**

| Tier | max_retries | base_delay | Rationale |
|------|-------------|------------|-----------|
| FREE | 2 | 2.0s | Lokale Ollama, minder load |
| BASIC | 3 | 1.5s | Groq is fast, quick retry |
| STANDARD | 3 | 1.0s | Balanced |
| PROFESSIONAL | 4 | 1.0s | Higher SLA expectation |
| PREMIUM | 5 | 0.5s | Fastest recovery |

### Component 2: Streaming Support

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Streaming Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ LLM API  │───▶│ AsyncGen     │───▶│ SSE Endpoint     │   │
│  │ (stream) │    │ (yield)      │    │ (EventSource)    │   │
│  └──────────┘    └──────────────┘    └──────────────────┘   │
│       │                 │                     │              │
│       ▼                 ▼                     ▼              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Ollama:  │    │ Token by     │    │ data: {"chunk":  │   │
│  │ stream:  │    │ token        │    │   "Hello"}       │   │
│  │ true     │    │ aggregation  │    │ data: {"chunk":  │   │
│  └──────────┘    └──────────────┘    │   " world"}      │   │
│                                       └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Streaming Methods:**

| Provider | Method | Implementation |
|----------|--------|----------------|
| Ollama | `stream: true` | Native JSON lines |
| Anthropic | `claude --stream` | CLI streaming mode |
| OpenAI | `stream=True` | SSE native |
| Groq | `stream=True` | SSE native |

**API Design:**

```
GET /api/v1/analysis/{id}/stream
Accept: text/event-stream

Response:
data: {"type": "chunk", "content": "The "}
data: {"type": "chunk", "content": "analysis "}
data: {"type": "chunk", "content": "shows..."}
data: {"type": "metadata", "tokens_so_far": 150}
data: {"type": "done", "total_tokens": 2500, "latency_ms": 12000}
```

### Component 3: Circuit Breaker Pattern

**Purpose:** Prevent cascading failures when a provider is unhealthy.

```
┌─────────────────────────────────────────────────────────────┐
│                    Circuit Breaker States                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│    ┌────────┐     5 failures     ┌────────┐                 │
│    │ CLOSED │ ─────────────────▶ │  OPEN  │                 │
│    │(normal)│                    │ (fail  │                 │
│    └────────┘                    │  fast) │                 │
│         ▲                        └────────┘                 │
│         │                             │                     │
│         │ success                     │ 30s timeout         │
│         │                             ▼                     │
│    ┌────────────┐              ┌────────────┐               │
│    │            │◀─────────────│ HALF-OPEN  │               │
│    │            │   success    │ (test 1    │               │
│    └────────────┘              │  request)  │               │
│                                └────────────┘               │
│                                      │                      │
│                                      │ failure              │
│                                      ▼                      │
│                                ┌────────┐                   │
│                                │  OPEN  │                   │
│                                └────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

**Circuit Breaker Configuration:**

```python
@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration per provider."""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 2        # Successes to close
    timeout_seconds: float = 30.0     # Time in OPEN state
    half_open_max_calls: int = 1      # Test calls in HALF_OPEN
```

---

## Implementation Plan

### Week 159 (Days 1-2): Retry Logic

| Task | Description | Hours | Tests |
|------|-------------|-------|-------|
| R1.1 | `RetryPolicy` dataclass | 1h | 3 |
| R1.2 | `call_with_retry()` base method | 3h | 10 |
| R1.3 | Jitter implementation | 1h | 3 |
| R2.1 | Integrate retry in `call_ollama()` | 2h | 5 |
| R2.2 | Integrate retry in `call_anthropic()` | 2h | 5 |
| R2.3 | Integrate retry in `call_llm()` dispatcher | 1h | 3 |
| R3.1 | Tier-based retry policies | 2h | 5 |
| R3.2 | Retry metrics/logging | 2h | 3 |

**Day 1 Deliverable:** Working retry logic with tests
**Day 2 Deliverable:** Tier integration + metrics

### Week 159-160 (Days 3-4): Streaming Support

| Task | Description | Hours | Tests |
|------|-------------|-------|-------|
| S1.1 | `call_ollama_streaming()` async generator | 3h | 5 |
| S1.2 | Token aggregation + metadata tracking | 2h | 3 |
| S2.1 | `call_anthropic_streaming()` | 3h | 5 |
| S2.2 | Streaming error handling | 2h | 3 |
| S3.1 | SSE streaming endpoint | 3h | 5 |
| S3.2 | Streaming progress events | 2h | 3 |
| S3.3 | Graceful stream cancellation | 2h | 3 |

**Day 3 Deliverable:** Ollama + Anthropic streaming
**Day 4 Deliverable:** SSE endpoints + integration

### Week 160 (Day 5): Circuit Breaker + Polish

| Task | Description | Hours | Tests |
|------|-------------|-------|-------|
| M1.1 | `CircuitBreaker` class | 3h | 8 |
| M1.2 | Circuit breaker per provider | 2h | 4 |
| M1.3 | Integration with health tracking | 2h | 3 |
| P1 | Documentation update | 1h | - |
| P2 | Integration tests | 2h | 5 |

---

## Deliverables

### New Files

| File | Description |
|------|-------------|
| `app/services/llm_resilience.py` | RetryPolicy, CircuitBreaker, call_with_retry |
| `app/routers/streaming.py` | SSE streaming endpoints |
| `tests/unit/services/test_llm_resilience.py` | Unit tests for resilience |
| `tests/unit/services/test_llm_streaming.py` | Unit tests for streaming |

### Modified Files

| File | Changes |
|------|---------|
| `app/services/extraction_llm_adapter.py` | Add streaming methods, integrate retry |
| `app/services/tier_provider_selector.py` | Add circuit breaker, retry policies |
| `app/config.py` | Add resilience configuration |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analysis/{id}/stream` | Stream analysis results (SSE) |
| GET | `/api/v1/providers/health` | Provider health + circuit state |
| POST | `/api/v1/providers/{id}/reset` | Reset circuit breaker |

---

## Success Criteria

### Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Failed analyses (retryable errors) | ~13% | <3% | Error logs |
| Time to first token | 30-60s | <5s | Latency metrics |
| Recovery from provider outage | Manual | Auto (<2min) | Incident logs |
| User-perceived responsiveness | Poor | Good | User feedback |

### Qualitative Criteria

- [ ] All LLM calls use retry logic by default
- [ ] Streaming available for Ollama and Anthropic
- [ ] Circuit breaker prevents cascading failures
- [ ] Retry attempts logged with proper context
- [ ] SSE endpoints work with standard EventSource clients

---

## Testing Strategy

### Unit Tests (~66 tests)

| Component | Tests | Focus |
|-----------|-------|-------|
| RetryPolicy | 8 | Configuration, validation |
| call_with_retry | 15 | Success, failure, retry scenarios |
| CircuitBreaker | 12 | State transitions, timing |
| Streaming (Ollama) | 10 | Chunks, errors, cancellation |
| Streaming (Anthropic) | 10 | CLI streaming, parsing |
| SSE Endpoints | 8 | Event format, headers, cancellation |
| Integration | 3 | End-to-end flows |

### Test Scenarios

**Retry Logic:**
```python
def test_retry_succeeds_on_second_attempt():
    """Test that transient failure is retried successfully."""

def test_retry_respects_max_retries():
    """Test that retries stop after max_retries."""

def test_retry_uses_exponential_backoff():
    """Test that delay increases exponentially."""

def test_non_retryable_error_fails_immediately():
    """Test that 400/401 errors are not retried."""
```

**Streaming:**
```python
def test_streaming_yields_chunks():
    """Test that streaming yields individual chunks."""

def test_streaming_handles_connection_drop():
    """Test graceful handling of connection drops."""

def test_streaming_aggregates_metadata():
    """Test that token counts are tracked during stream."""
```

**Circuit Breaker:**
```python
def test_circuit_opens_after_failures():
    """Test circuit opens after failure_threshold failures."""

def test_circuit_half_opens_after_timeout():
    """Test circuit transitions to HALF_OPEN after timeout."""

def test_circuit_closes_after_success():
    """Test circuit closes after success_threshold successes."""
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Retry storms under load | Medium | High | Jitter + circuit breaker |
| Streaming memory usage | Low | Medium | Chunk size limits |
| Breaking existing calls | Low | High | Backward compatible API |
| Circuit breaker too aggressive | Medium | Medium | Configurable thresholds |

---

## Dependencies

### Required
- `aiohttp` (already installed) - Async HTTP client
- `asyncio` (stdlib) - Async primitives

### Optional
- `tenacity` - Could replace custom retry logic (not recommended for control)

---

## Rollback Plan

1. Feature flags for retry/streaming (default: enabled)
2. If issues: disable via config without deployment
3. All changes backward compatible (existing `call_*` methods unchanged)

---

## Future Enhancements (Out of Scope)

- [ ] Adaptive retry based on historical success rates
- [ ] Provider failover chains (Ollama → Groq → OpenAI)
- [ ] Streaming for all providers (Google, OpenAI, Groq)
- [ ] WebSocket alternative to SSE
- [ ] Client-side retry coordination

---

## References

- [Exponential Backoff and Jitter (AWS)](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Ollama API Streaming](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion)

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-01-19 | Claude Code | Initial specification |
