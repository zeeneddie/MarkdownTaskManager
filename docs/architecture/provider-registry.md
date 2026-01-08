# Provider Registry & Multi-LLM Architecture

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 54 COMPLETE
**Last Updated:** 2025-12-17

---

## Overview

De Provider Registry is de centrale abstractielaag voor alle LLM providers. Het systeem ondersteunt 7 providers met 15+ models en cost-optimized routing.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-MODEL LAYER (7 Providers)                       │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  TIER 1: FREE (Local)                                               ││
│  │  ┌─────────────────────────────────────────────────────────┐        ││
│  │  │ Ollama: qwen2.5-coder, deepseek-r1, codellama, mistral  │        ││
│  │  └─────────────────────────────────────────────────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  TIER 2: ULTRA-CHEAP ($0.05-$0.15/M)                                ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            ││
│  │  │ Gemini Flash- │  │ Qwen Turbo   │  │ Groq Llama    │            ││
│  │  │ Lite $0.075   │  │ $0.05        │  │ 3.1 $0.05     │            ││
│  │  └───────────────┘  └───────────────┘  └───────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  TIER 3: CHEAP ($0.30-$0.60/M)                                      ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            ││
│  │  │ Gemini Flash  │  │ Qwen Plus    │  │ Groq Qwen3    │            ││
│  │  │ $0.30         │  │ $0.40        │  │ 32B $0.29     │            ││
│  │  └───────────────┘  └───────────────┘  └───────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  TIER 4: MID ($1.00-$2.00/M)                                        ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            ││
│  │  │ OpenAI GPT-   │  │ Gemini Pro   │  │ Moonshot     │            ││
│  │  │ 5.2 $1.75     │  │ $1.25        │  │ Kimi K2 $1   │            ││
│  │  └───────────────┘  └───────────────┘  └───────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  TIER 5: PREMIUM ($5.00+/M)                                         ││
│  │  ┌───────────────┐  ┌───────────────┐                               ││
│  │  │ Anthropic     │  │ Gemini 3 Pro │                               ││
│  │  │ Opus 4.5 $5   │  │ $2.00        │                               ││
│  │  └───────────────┘  └───────────────┘                               ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Provider Details (7)

| Provider | Models | Cost Range | Context | Specialty |
|----------|--------|------------|---------|-----------|
| **Ollama** | qwen2.5-coder, deepseek-r1, codellama, mistral | FREE | 128K | Local, privacy |
| **Google Gemini** | Flash-Lite, Flash, Pro, 3-Pro | $0.08-$2.00/M | 1M | Cross-validation |
| **Alibaba Qwen** | Turbo, Plus | $0.05-$0.40/M | 1M | Bulk analysis |
| **Groq** | Llama 3.1/3.3, Qwen3-32B | $0.05-$0.60/M | 128K | Fast (840 TPS) |
| **OpenAI** | GPT-5.2 | $1.75/$14/M | 128K | Coding specialist |
| **Moonshot** | Kimi K2 | $1.00/$3.00/M | 200K | 1T parameters |
| **Anthropic** | Claude Opus 4.5 | $5.00/$25/M | 200K | Deep reasoning |

---

## Provider Registry Implementation

```python
# Located in: backend/app/providers/

class LLMProvider:
    name: str           # "ollama", "gemini", "qwen", "groq", "openai", "moonshot", "anthropic"
    tier: str           # "free", "ultra-cheap", "cheap", "mid", "premium"
    cost_input: float   # per million tokens
    cost_output: float  # per million tokens
    is_local: bool      # True for Ollama
    is_active: bool
    context_limit: int  # e.g., 128K, 200K, 1M
    config: Dict        # model-specific settings
```

### Implemented Providers

| File | Provider | Status |
|------|----------|--------|
| `ollama_provider.py` | OllamaProvider | COMPLETE |
| `gemini_provider.py` | GeminiProvider | COMPLETE |
| `qwen_provider.py` | QwenProvider | COMPLETE |
| `groq_provider.py` | GroqProvider | COMPLETE |
| `openai_provider.py` | OpenAIProvider | COMPLETE |
| `moonshot_provider.py` | MoonshotProvider | COMPLETE |
| `anthropic_provider.py` | AnthropicProvider | COMPLETE |

---

## Task → Model Routing

### Cost-Optimized Routing Strategy

```python
TASK_TO_MODEL = {
    # Tier 1: FREE (Ollama local)
    "simple_generation": "ollama/qwen2.5-coder:7b",
    "quick_fix": "ollama/qwen2.5-coder:7b",
    "documentation": "ollama/mistral:latest",
    "debugging": "ollama/codellama:latest",
    "business_logic": "ollama/deepseek-r1:latest",

    # Tier 2: ULTRA-CHEAP ($0.05-$0.15/M)
    "bulk_scan": "gemini/flash-lite",
    "integration_map": "qwen/turbo",
    "fast_validation": "groq/llama-3.1-8b",

    # Tier 3: CHEAP ($0.30-$0.60/M)
    "cross_validation": "gemini/flash",
    "large_context": "qwen/plus",
    "fast_reasoning": "groq/qwen3-32b",

    # Tier 4: MID ($1.00-$2.00/M)
    "code_review": "openai/gpt-5.2",
    "coding_complex": "gemini/pro",
    "mega_model": "moonshot/kimi-k2",
    "agentic": "gemini/3-pro",

    # Tier 5: PREMIUM ($5.00+/M)
    "architecture": "anthropic/opus-4.5",
    "security_audit": "anthropic/opus-4.5",
    "complex_analysis": "anthropic/opus-4.5",
}
```

### Agent → Model Mapping

| Agent | Primary Model | Fallback Model | Use Case |
|-------|---------------|----------------|----------|
| Felix | qwen2.5-coder:7b | gemini/pro | Architecture |
| Quinn | deepseek-r1 | anthropic/opus-4.5 | Quality review |
| Betty | codellama | openai/gpt-5.2 | Debugging |
| Eliza | deepseek-r1 | gemini/pro | Estimation |
| Diana | mistral | qwen/plus | Documentation |
| Marcus | qwen2.5-coder:7b | gemini/flash | Maintenance |
| Tessa | qwen2.5-coder:7b | gemini/flash | Testing |
| Miguel | qwen2.5-coder:7b | gemini/pro | Migration |
| Peter | deepseek-r1 | anthropic/opus-4.5 | Product |
| Paul | qwen2.5:7b | gemini/flash | Planning |

---

## Stack Agent Factory

```python
# Template-based agent instantiation per tech-stack
STACK_AGENTS = {
    "python": ["BackendDev_py", "CodeRev_py", "SecAudit_py", "Tester_py"],
    "javascript": ["BackendDev_js", "FrontendDev_js", "CodeRev_js", "SecAudit_js", "Tester_js"],
    "go": ["BackendDev_go", "CodeRev_go", "SecAudit_go", "Tester_go"],
    "rust": ["BackendDev_rs", "CodeRev_rs", "SecAudit_rs", "Tester_rs"],
    "dotnet": ["BackendDev_cs", "CodeRev_cs", "SecAudit_cs", "Tester_cs"],
}

def create_stack_agent(stack: str, role: str, project_id: UUID) -> StackAgent:
    """Instantiate stack-specific agent from template."""
    template = AGENT_TEMPLATES[role]
    return StackAgent(
        name=f"{role}_{stack}",
        stack=stack,
        project_id=project_id,
        prompt_template=template.get_prompt(stack),
        model=template.get_model(stack),
        capabilities=template.get_capabilities(stack),
    )
```

---

## Customer Extraction Tiers

Voor de Deep Extraction Pipeline gebruiken we tier-based LLM routing:

| Tier | Price | LLMs Used | Confidence |
|------|-------|-----------|------------|
| **FREE** | $0 | 3 (Ollama only) | 60% |
| **BASIC** | $5 | 5 (+Groq, Qwen) | 70% |
| **STANDARD** | $25 | 7 (+Gemini) | 80% |
| **PROFESSIONAL** | $75 | 9 (+GPT-5.2) | 90% |
| **PREMIUM** | $150 | 10 (+Opus) | 95% |

*Prijzen per 50K LOC*

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET | List all providers |
| `/api/providers/{name}` | GET | Get provider details |
| `/api/providers/{name}/models` | GET | List models for provider |
| `/api/providers/route` | POST | Get optimal model for task |
| `/api/providers/cost` | POST | Estimate cost for task |

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [deep-extraction-pipeline.md](./deep-extraction-pipeline.md) - Multi-LLM extraction
- [llm-council.md](./llm-council.md) - LLM Council consensus
