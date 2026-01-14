# Technical Debt Backlog & Evaluations

**Last Updated:** 2026-01-13

---

## Technical Debt Items

| Task | Effort | Priority | Notes |
|------|--------|----------|-------|
| **FP Methodology Fix** | 36 uur | **CRITICAL** | See [Fase 22](fase-22-fp-methodology.md) - NESMA/IFPUG violations make estimates indefensible |
| **Pydantic V2 Migration** | 8-16 uur | Medium | Breaking changes in validators, model_validator etc. |
| **FastAPI Lifespan Handlers** | 2 uur | Low | Replace deprecated on_event with lifespan context manager |
| **datetime.utcnow() deprecation** | 2 uur | Low | Use timezone-aware datetimes (datetime.now(UTC)) |
| **Falcon H1R 7B Integration** | 8 uur | Medium | New reasoning model for code analysis (see below) |

---

## Potential LLM Provider Addition: Falcon H1R 7B

**Status:** EVALUATION
**Source:** TII Abu Dhabi (Technology Innovation Institute)
**Release Date:** January 5, 2026
**License:** Falcon LLM License 1.0 (Apache 2.0 based, commercial use allowed)

### Why Falcon H1R 7B?

| Feature | Value | Benefit for MarQed |
|---------|-------|-------------------|
| **Parameters** | 7B | Lokaal draaibaar via Ollama |
| **Context Window** | 256k tokens | Kan hele legacy codebases analyseren |
| **Architecture** | Hybrid Transformer + Mamba2 | 2x sneller dan Qwen3-8B |
| **Math Performance** | 88.1% AIME-24 | Sterke logica voor FP berekeningen |
| **Code Performance** | 68.6% LiveCodeBench | Best-in-class voor <8B modellen |
| **Throughput** | ~1,500 tok/s @ batch 64 | Snel voor batch analyses |

### Benchmark Vergelijking

| Benchmark | Falcon H1R 7B | Qwen3 8B | Phi 4 14B |
|-----------|---------------|----------|-----------|
| AIME 24 | **88.1%** | ~75% | 86.2% |
| MMLU Pro | 72.1% | ~70% | ~74% |
| LiveCodeBench v6 | **68.6%** | ~60% | ~65% |
| Context Window | **256k** | 32k | 128k |

### Potentiële Rol in MarQed

| Use Case | Geschiktheid | Notes |
|----------|--------------|-------|
| **Code Analysis (FREE tier)** | Excellent | Vervangt/verbetert Ollama tier |
| **FP Calculation** | Excellent | Sterke math reasoning |
| **Long Context Analysis** | Excellent | 256k voor grote codebases |
| **Stability Detection** | Good | Pattern recognition |
| **LLM Council Participant** | Good | Diversiteit in council |

### Integration Plan

```
Week N: Falcon H1R 7B Integration (8 uur)
├── Download model via Hugging Face
├── Setup Ollama modelfile
├── Add FalconProvider to llm_providers/
├── Configure tier routing (FREE/BASIC)
├── Benchmark against current Ollama models
└── Update LLM Council weights
```

### Hardware Requirements (Estimated)

| Config | VRAM | Speed |
|--------|------|-------|
| FP16 | ~14GB | ~500 tok/s |
| INT8 | ~8GB | ~400 tok/s |
| INT4 (GGUF) | ~4GB | ~300 tok/s |

### References

| Source | URL |
|--------|-----|
| Hugging Face | [huggingface.co/tiiuae/Falcon-H1R-7B](https://huggingface.co/tiiuae/Falcon-H1R-7B) |
| TII Blog | [falcon-lm.github.io/blog/falcon-h1r-7b](https://falcon-lm.github.io/blog/falcon-h1r-7b/) |
| VentureBeat | [venturebeat.com](https://venturebeat.com/technology/tiis-falcon-h1r-7b-can-out-reason-models-up-to-7x-its-size-and-its-mostly) |
| MarkTechPost | [marktechpost.com](https://www.marktechpost.com/2026/01/07/tii-abu-dhabi-released-falcon-h1r-7b-a-new-reasoning-model-outperforming-others-in-math-and-coding-with-only-7b-params-with-256k-context-window/) |

---

## Pydantic V2 Migration Details

### Breaking Changes to Address

```python
# OLD (Pydantic V1)
class MyModel(BaseModel):
    @validator('field')
    def validate_field(cls, v):
        return v

# NEW (Pydantic V2)
class MyModel(BaseModel):
    @field_validator('field')
    @classmethod
    def validate_field(cls, v):
        return v
```

### Files Affected (Estimated)
- `app/models/*.py` - ~50 files
- `app/services/*.py` - ~30 files with embedded models
- `app/api/*.py` - Request/Response models

### Migration Strategy
1. Install `bump-pydantic` tool
2. Run automatic migration
3. Manual review of edge cases
4. Update tests
5. Validate all endpoints

---

## FastAPI Lifespan Migration

### Current (Deprecated)
```python
@app.on_event("startup")
async def startup():
    # initialization

@app.on_event("shutdown")
async def shutdown():
    # cleanup
```

### Target (Lifespan)
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI(lifespan=lifespan)
```

---

## datetime.utcnow() Deprecation

### Current (Deprecated)
```python
from datetime import datetime
created_at = datetime.utcnow()
```

### Target (Timezone-Aware)
```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

### Files Affected
- All service files using `datetime.utcnow()`
- Database models with default timestamps
- Test fixtures

---

← [Back to Overview](../phases-planned.md)
