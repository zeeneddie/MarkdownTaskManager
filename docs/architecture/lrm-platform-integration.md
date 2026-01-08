# LRM & Platform Integration Research

**Status:** RESEARCH COMPLETE | Decision Required
**Compiled:** 2026-01-04
**Parent Document:** [ROADMAP.md](../../ROADMAP.md)

---

## Executive Summary

Dit document bevat de complete research naar **Large Reasoning Models (LRM)** en **Open Source Hosting Platforms** voor integratie in het MarQed AI Agent Platform. Het biedt concrete keuze-opties voor:

1. **LRM Providers** - Reasoning models voor onderhoud, migratie en bouwen van software
2. **Multi-LLM Orchestratie** - Frameworks voor provider-agnostische integratie
3. **Code Hosting Platforms** - Alternatieven voor project hosting

---

## Deel 1: Large Reasoning Models (LRM)

### Wat zijn LRMs?

Large Reasoning Models zijn AI-modellen getraind met **Reinforcement Learning** om multi-step reasoning uit te voeren. Ze gebruiken **Chain-of-Thought (CoT)** om complexe problemen op te lossen voordat ze een antwoord geven.

**Kenmerkend:**
- `<think>...</think>` reasoning blocks
- Self-verification en reflection
- Significant betere prestaties op math, code, en logica taken

### Open Source LRM Landschap (2025-2026)

#### Tier 1: Frontier Open Source Reasoning Models

| Model | Parameters | Licentie | Benchmark | Platform | Use Case |
|-------|-----------|----------|-----------|----------|----------|
| [**DeepSeek-R1**](https://github.com/deepseek-ai/DeepSeek-R1) | 671B (MoE) | MIT | ~o1-level | Ollama, HF | Deep reasoning, complex analysis |
| [**DeepSeek-R1-Distill-Qwen-32B**](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) | 32B | Apache 2.0 | > o1-mini | Ollama, HF | Lokaal reasoning, code review |
| [**QwQ-32B**](https://huggingface.co/Qwen/QwQ-32B) | 32B | Apache 2.0 | ~o1-mini | Ollama, HF | Complexe beslissingen |
| [**Qwen3-Coder-480B**](https://github.com/QwenLM/Qwen3-Coder) | 480B (35B active) | Apache 2.0 | 69.6% SWE-Bench | HF, ModelScope | Agentic coding |
| [**Open-R1**](https://github.com/huggingface/open-r1) | 7B+ | Apache 2.0 | HF reproduction | HF | Lightweight reasoning |

#### Tier 2: Coding-Specifieke Models

| Model | Focus | Best For |
|-------|-------|----------|
| [**Qwen2.5-Coder-32B**](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) | Multi-language code | Code generation, refactoring |
| [**DeepCoder-14B**](https://huggingface.co/agentica-org/DeepCoder-14B-Preview) | Competitive coding | Complex algorithms |
| [**CodeLlama-70B**](https://huggingface.co/meta-llama/CodeLlama-70b-hf) | Code completion | Legacy code analyse |
| [**StarCoder2-15B**](https://huggingface.co/bigcode/starcoder2-15b) | Transparant getraind | Multi-language support |
| [**GLM-4.7**](https://github.com/THUDM/GLM-4) | Agent-style execution | Multi-step workflows |

### Development vs Production Environment

#### Development Environment (Geen GPU / Minimal GPU)

**Use Case:** Lokale ontwikkeling, CI/CD pipelines, resource-constrained servers.

| Model | Parameters | VRAM | RAM (CPU) | Speed | Best For |
|-------|-----------|------|-----------|-------|----------|
| **qwen2.5-coder:3b** | 3B | 2GB | 6GB | Fast | Quick code gen, prototyping |
| **qwen2.5-coder:7b** | 7B | 4GB | 10GB | Medium | Code review, refactoring |
| **deepseek-r1:1.5b** | 1.5B | 2GB | 4GB | Fast | Simple reasoning |
| **deepseek-r1:7b** | 7B | 4GB | 10GB | Medium | Basic reasoning tasks |
| **codellama:7b** | 7B | 4GB | 10GB | Medium | Code completion |
| **mistral:7b** | 7B | 4GB | 10GB | Medium | Documentation, general |
| **qwen2.5:3b** | 3B | 2GB | 6GB | Fast | Bulk processing |

**Configuratie:**
```yaml
# Development profile - CPU/Minimal GPU
development:
  ollama_models:
    - qwen2.5-coder:7b    # Primary coding
    - deepseek-r1:7b      # Basic reasoning
    - codellama:7b        # Debug
    - mistral:7b          # Docs
  hardware:
    min_ram: 16GB
    gpu: Optional (8GB VRAM max)
    cpu: 8+ cores recommended
  quantization: Q4_K_M (smaller, faster)
```

**Kenmerken:**
- ✅ Draait op laptop/workstation zonder GPU
- ✅ Geschikt voor CI/CD runners (GitHub Actions, GitLab CI)
- ✅ Snelle iteratiecycli
- ⚠️ Lagere reasoning kwaliteit
- ⚠️ Context window beperkt (4K-8K effectief)

#### Production Environment (GPU Vereist)

**Use Case:** Productie reasoning, klant-facing analyses, diepgaande migratie planning.

| Model | Parameters | VRAM | Speed | Best For |
|-------|-----------|------|-------|----------|
| **deepseek-r1:32b-distill** | 32B | 20GB | Medium | Deep reasoning, analysis |
| **qwq:32b** | 32B | 20GB | Medium | Complex decisions |
| **qwen2.5-coder:32b** | 32B | 20GB | Medium | Large codebase analysis |
| **qwen3-coder:32b** | 32B | 20GB | Medium | Agentic coding |
| **codellama:34b** | 34B | 22GB | Slow | Complex debugging |
| **deepseek-r1:70b** | 70B | 40GB | Slow | Maximum reasoning |
| **codellama:70b** | 70B | 40GB | Slow | Enterprise code analysis |

**Configuratie:**
```yaml
# Production profile - GPU Required
production:
  ollama_models:
    - deepseek-r1:32b-distill  # Primary reasoning
    - qwq:32b                   # Decision support
    - qwen3-coder:32b           # Agentic coding
    - codellama:34b             # Complex debug
  hardware:
    gpu: Required
    min_vram: 24GB (RTX 4090, A100-40GB)
    recommended: 48GB+ (A100-80GB, H100)
    ram: 64GB+
  quantization: Q8_0 (quality) or FP16 (max quality)
```

**Kenmerken:**
- ✅ Chain-of-thought reasoning (`<think>` blocks)
- ✅ 128K+ context window
- ✅ Near-o1 performance op complexe taken
- ⚠️ Vereist dedicated GPU server
- ⚠️ Hogere energie/kosten

#### Hybrid Strategy: Dev → Prod Promotion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DEVELOPMENT → PRODUCTION WORKFLOW                                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  DEVELOPMENT (No GPU)                    PRODUCTION (GPU)               ││
│  │  ┌─────────────────────┐                ┌─────────────────────┐         ││
│  │  │ qwen2.5-coder:7b    │  ─── Test ───► │ qwen3-coder:32b     │         ││
│  │  │ deepseek-r1:7b      │  ─── Pass ───► │ deepseek-r1:32b     │         ││
│  │  │ codellama:7b        │  ─────────────►│ codellama:34b       │         ││
│  │  └─────────────────────┘                └─────────────────────┘         ││
│  │                                                                          ││
│  │  Use Case: Iteration,    │               Use Case: Client delivery,     ││
│  │  prototyping, CI/CD      │               deep analysis, final QA        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  MODEL EQUIVALENTS:                                                          │
│  Development          Production        Capability Gain                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  qwen2.5-coder:7b  →  qwen3-coder:32b   4.5x params, agentic capabilities   │
│  deepseek-r1:7b    →  deepseek-r1:32b   CoT reasoning, self-verification    │
│  codellama:7b      →  codellama:34b     Better context, complex patterns    │
│  mistral:7b        →  mistral:7b        Same (sufficient for docs)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Agent Environment Mapping

| Agent | Development Model | Production Model | Notes |
|-------|-------------------|------------------|-------|
| **Felix** | qwen2.5-coder:7b | qwen3-coder:32b | Upgrade for architecture decisions |
| **Quinn** | deepseek-r1:7b | deepseek-r1:32b-distill | Critical: needs CoT for quality |
| **Betty** | codellama:7b | codellama:34b | Optional: 7b often sufficient |
| **Eliza** | deepseek-r1:7b | qwq:32b | Upgrade for estimation accuracy |
| **Diana** | mistral:7b | mistral:7b | Same: sufficient for docs |
| **Marcus** | qwen2.5-coder:7b | qwen2.5-coder:32b | Upgrade for complex refactoring |
| **Tessa** | qwen2.5-coder:7b | qwen3-coder:32b | Upgrade for test generation |
| **Miguel** | qwen2.5-coder:7b | qwen3-coder:32b | Critical: migration planning |
| **Peter** | deepseek-r1:7b | qwq:32b | Upgrade for product decisions |
| **Paul** | qwen2.5:7b | qwq:32b | Upgrade for sprint planning |
| **Vicky** | mistral:7b | mistral:7b | Same: design specs |

---

### Keuze-Opties: LRM Provider Strategy

#### Optie A: Ollama-First (Aanbevolen)

**Strategie:** Maximaal lokaal draaien, cloud alleen voor premium taken.

```
┌─────────────────────────────────────────────────────────────────────┐
│  OPTIE A: OLLAMA-FIRST                                               │
│                                                                      │
│  PRIMARY (Lokaal - FREE)                     VRAM Required           │
│  ├── deepseek-r1:32b-distill    Reasoning   ~20GB                   │
│  ├── qwq:32b                    Decisions   ~20GB                   │
│  ├── qwen2.5-coder:32b          Code Gen    ~20GB                   │
│  └── codellama:34b              Debugging   ~20GB                   │
│                                                                      │
│  FALLBACK (Cloud - Budget)                                          │
│  ├── Groq: qwen3-32b            Fast        $0.29/M tokens          │
│  └── Groq: llama-3.1-70b        General     $0.59/M tokens          │
│                                                                      │
│  PREMIUM (Cloud - Quality)                                          │
│  └── Claude Opus 4.5            Synthesis   $5.00/$25/M tokens      │
│                                                                      │
│  Geschatte Kosten: $0-50/maand (afhankelijk van premium gebruik)    │
│  Hardware Vereist: GPU met 24GB+ VRAM (RTX 4090, A100)              │
└─────────────────────────────────────────────────────────────────────┘
```

**Voordelen:**
- Geen recurring cloud kosten voor standaard werk
- Privacy: code verlaat nooit de server
- Geen rate limits of API outages

**Nadelen:**
- Vereist GPU hardware ($1500-2000 initieel)
- Minder flexibel bij piekbelasting

#### Optie B: Hybrid Cloud

**Strategie:** Cloud voor reasoning, lokaal voor bulk.

```
┌─────────────────────────────────────────────────────────────────────┐
│  OPTIE B: HYBRID CLOUD                                               │
│                                                                      │
│  REASONING (Cloud - Pay per use)                                    │
│  ├── Groq: deepseek-r1-distill  Fast        $0.14/M tokens          │
│  ├── Groq: qwen3-32b            Reasoning   $0.29/M tokens          │
│  └── Fireworks: qwen3-coder     Agentic     $0.20/M tokens          │
│                                                                      │
│  BULK (Lokaal - FREE)                                               │
│  ├── qwen2.5-coder:7b           Code Gen    ~4GB VRAM               │
│  └── codellama:7b               Debugging   ~4GB VRAM               │
│                                                                      │
│  PREMIUM (Cloud - Quality)                                          │
│  └── Claude Opus 4.5            Synthesis   $5.00/$25/M tokens      │
│                                                                      │
│  Geschatte Kosten: $50-200/maand                                    │
│  Hardware Vereist: Standaard workstation (8GB+ VRAM)                │
└─────────────────────────────────────────────────────────────────────┘
```

**Voordelen:**
- Lagere hardware investering
- Snelle inference via Groq (840 tokens/sec)
- Flexibel schaalbaar

**Nadelen:**
- Recurring cloud kosten
- Afhankelijk van externe providers

#### Optie C: Full Cloud (Enterprise)

**Strategie:** Volledig cloud-based, geen lokale GPU.

```
┌─────────────────────────────────────────────────────────────────────┐
│  OPTIE C: FULL CLOUD                                                 │
│                                                                      │
│  REASONING                                                          │
│  ├── OpenAI: o3-mini            Best        $1.10/M tokens          │
│  ├── Anthropic: Claude 3.5      Balanced    $3.00/$15/M tokens      │
│  └── Google: Gemini 2.5 Pro     Fast        $1.25/M tokens          │
│                                                                      │
│  CODING                                                             │
│  ├── OpenAI: GPT-5.2            Deep        $1.75/$14/M tokens      │
│  └── Anthropic: Claude Opus     Synthesis   $5.00/$25/M tokens      │
│                                                                      │
│  Geschatte Kosten: $200-500/maand                                   │
│  Hardware Vereist: Geen GPU nodig                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Voordelen:**
- Geen hardware investering
- Altijd nieuwste models
- Simpele setup

**Nadelen:**
- Hoogste recurring kosten
- Privacy concerns met proprietary code
- Vendor lock-in risico

### Aanbeveling: Optie A (Ollama-First)

Voor MarQed's use case (onderhoud, migratie, bouwen) is **Optie A** aanbevolen omdat:
1. **Privacy**: Klantcode blijft lokaal
2. **Kosten**: Eenmalige hardware vs recurring cloud
3. **Performance**: Geen rate limits bij intensief gebruik
4. **Huidige setup**: Al Ollama geïntegreerd (deepseek-r1, qwen2.5-coder)

---

## Deel 2: Multi-LLM Orchestratie Frameworks

### Framework Vergelijking

| Framework | Type | Multi-Provider | Best For | GitHub |
|-----------|------|----------------|----------|--------|
| [**LiteLLM**](https://github.com/BerriAI/litellm) | Proxy/Gateway | 100+ providers | Provider-agnostisch API | 18k+ stars |
| [**LangChain/LangGraph**](https://github.com/langchain-ai/langchain) | Framework | Via adapters | Complex stateful workflows | 98k+ stars |
| [**CrewAI**](https://github.com/crewAIInc/crewAI) | Orchestration | Via LiteLLM | Role-based agent teams | 25k+ stars |
| [**AutoGen**](https://github.com/microsoft/autogen) | Multi-agent | OpenAI-compatible | Conversations, research | 40k+ stars |
| [**smolagents**](https://github.com/huggingface/smolagents) | Agents | LiteLLM, HF API | Code-writing agents | 15k+ stars |
| [**OpenLLM**](https://github.com/bentoml/OpenLLM) | Serving | Self-hosted | Production deployment | 10k+ stars |
| [**Langroid**](https://github.com/langroid/langroid) | Multi-agent | LiteLLM proxy | Collaborative agents | 3k+ stars |

### Keuze-Opties: Orchestratie Framework

#### Optie 1: LiteLLM Integration (Aanbevolen)

**Voeg LiteLLM toe als abstractielaag boven huidige Provider Registry.**

```python
# Huidige situatie: Direct provider calls
response = await ollama_provider.generate(prompt)

# Met LiteLLM: Unified API
from litellm import completion

response = completion(
    model="ollama/deepseek-r1",  # of "groq/qwen3-32b", "anthropic/claude-3"
    messages=[{"role": "user", "content": prompt}]
)
```

**Voordelen:**
- 100+ providers via één API
- Built-in cost tracking, caching, fallbacks
- Minimale refactoring van bestaande code
- OpenAI-compatible endpoints

**Implementatie:**
```
backend/
├── app/
│   ├── providers/
│   │   ├── litellm_gateway.py      # NEW: LiteLLM wrapper
│   │   ├── registry.py             # MODIFY: Route via LiteLLM
│   │   └── ...existing providers
│   └── services/
│       └── llm_council_service.py  # MODIFY: Use LiteLLM
```

**Effort:** 2-3 dagen

#### Optie 2: CrewAI voor Agent Orchestratie

**Vervang/complement huidige agent workflows met CrewAI.**

```python
from crewai import Agent, Task, Crew

felix = Agent(
    role="Feature Architect",
    goal="Design system architecture",
    backstory="Senior architect with DDD expertise",
    llm="ollama/qwen2.5-coder:32b"
)

quinn = Agent(
    role="Quality Inspector",
    goal="Ensure code quality and security",
    backstory="Security expert with OWASP knowledge",
    llm="ollama/deepseek-r1"
)

crew = Crew(agents=[felix, quinn], tasks=[...])
result = crew.kickoff()
```

**Voordelen:**
- Role-based agent orchestratie out-of-the-box
- Hierarchical en sequential processes
- Memory en context sharing

**Nadelen:**
- Significante refactoring van bestaande agents
- Nieuwe dependency

**Effort:** 2-3 weken

#### Optie 3: Behoud Huidige Architectuur + LRM Upgrade

**Minimale wijziging: Alleen LRM models toevoegen aan bestaande Provider Registry.**

```python
# provider_registry.py - extend MODELS dict
MODELS = {
    # Existing
    "deepseek-r1": OllamaProvider("deepseek-r1"),
    "qwen2.5-coder:7b": OllamaProvider("qwen2.5-coder:7b"),

    # NEW: LRM additions
    "deepseek-r1:32b-distill": OllamaProvider("deepseek-r1:32b-distill"),
    "qwq:32b": OllamaProvider("qwq:32b"),
    "qwen3-coder:32b": OllamaProvider("qwen3-coder:32b"),
}
```

**Voordelen:**
- Minimale wijziging
- Geen nieuwe dependencies
- Backward compatible

**Nadelen:**
- Geen extra features (cost tracking, fallbacks)
- Handmatig provider management

**Effort:** 1 dag

### Aanbeveling: Optie 1 (LiteLLM) + Optie 3 (LRM Upgrade)

Combineer:
1. **LiteLLM** voor unified API en cost tracking
2. **LRM model upgrade** voor betere reasoning

---

## Deel 3: Open Source Hosting Platforms

### Platform Categorieën

#### Mainstream Platforms

| Platform | Type | Bijzonderheden |
|----------|------|----------------|
| [**GitHub**](https://github.com) | Hosted | Microsoft-eigendom, 100M+ developers |
| [**GitLab**](https://gitlab.com) | Hosted + Self-hosted | MIT (CE), volledige DevOps |
| [**Bitbucket**](https://bitbucket.org) | Hosted | Atlassian, Jira integratie |
| [**Azure DevOps**](https://azure.microsoft.com/en-us/products/devops) | Hosted | Microsoft enterprise |

#### Open Source Self-Hosted

| Platform | Licentie | Taal | Resources | Best For |
|----------|----------|------|-----------|----------|
| [**Forgejo**](https://forgejo.org) | GPL-3.0 | Go | 1GB RAM | Community-governed, Gitea fork |
| [**Gitea**](https://gitea.io) | MIT | Go | 1GB RAM | Lightweight, Actions CI/CD |
| [**GitLab CE**](https://gitlab.com/gitlab-org/gitlab) | MIT | Ruby | 4GB+ RAM | Full DevOps platform |
| [**OneDev**](https://onedev.io) | MIT | Java | 2GB RAM | Code intelligence, visual pipelines |
| [**Gogs**](https://gogs.io) | MIT | Go | 512MB RAM | Ultra-minimal |

#### Community-Hosted (Gratis)

| Platform | Basis | Focus |
|----------|-------|-------|
| [**Codeberg**](https://codeberg.org) | Forgejo | EU privacy, non-profit, 300K+ repos |
| [**SourceHut**](https://sr.ht) | Custom | Mailing list workflow, minimalist |
| [**NotABug**](https://notabug.org) | Gogs | Freedom-focused |
| [**Framagit**](https://framagit.org) | GitLab CE | French non-profit |

#### Gedecentraliseerd

| Platform | Technologie | Bijzonderheden |
|----------|-------------|----------------|
| [**Radicle**](https://radicle.xyz) | P2P + Git | Geen centrale server, cryptografisch |
| [**ForgeFed**](https://forgefed.org) | ActivityPub | Federated forge protocol |

#### Regionaal

| Platform | Regio | Bijzonderheden |
|----------|-------|----------------|
| [**Gitee**](https://gitee.com) | China | 13.5M+ developers, 60% Chinese markt |
| [**CSDN GitCode**](https://gitcode.net) | China | CSDN community |
| [**GNU Savannah**](https://savannah.gnu.org) | FSF | Stricte vrije software policy |

### Keuze-Opties: Hosting Platform

#### Optie A: GitHub (Status Quo)

**Blijf bij GitHub voor publieke en private repositories.**

**Voordelen:**
- Maximale visibility voor open source
- GitHub Actions CI/CD
- Integratie met bestaande tooling
- Copilot, Codespaces

**Nadelen:**
- Microsoft-eigendom
- Geen data sovereignty
- Vendor lock-in

**Use Case:** Publieke open source projecten

#### Optie B: Self-Hosted Forgejo/Gitea

**Host eigen forge voor private/klant projecten.**

```yaml
# docker-compose.forgejo.yml
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:9
    ports:
      - "3000:3000"
      - "22:22"
    volumes:
      - ./forgejo-data:/data
    environment:
      - USER_UID=1000
      - USER_GID=1000
```

**Voordelen:**
- Volledige controle over data
- GDPR compliance
- Geen externe afhankelijkheden
- Forgejo Actions (GitHub-compatible)

**Nadelen:**
- Hosting/maintenance overhead
- Geen externe contributors via platform

**Use Case:** Private klantprojecten, enterprise

#### Optie C: Codeberg voor Open Source

**Gebruik Codeberg voor open source, self-hosted voor private.**

**Voordelen:**
- EU-based non-profit
- Privacy-first
- Geen ads/tracking
- Gratis voor open source

**Nadelen:**
- Minder bekend dan GitHub
- Kleinere community

**Use Case:** Privacy-gevoelige open source

#### Optie D: Hybrid Strategie (Aanbevolen)

```
┌─────────────────────────────────────────────────────────────────────┐
│  HYBRID HOSTING STRATEGIE                                           │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │  GitHub             │  │  Self-Hosted        │                   │
│  │  (Public)           │  │  Forgejo (Private)  │                   │
│  ├─────────────────────┤  ├─────────────────────┤                   │
│  │ • MarQed Platform   │  │ • Klant projecten   │                   │
│  │ • Open source tools │  │ • HCI-CRS migratie  │                   │
│  │ • Documentation     │  │ • Proprietary code  │                   │
│  │ • Community contribs│  │ • Internal tools    │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                      │
│  MIRROR: Codeberg (backup + EU presence)                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Implementatie:**
1. GitHub: Publiek platform, community, visibility
2. Forgejo: Private klantprojecten, EU data
3. Codeberg: Mirror voor EU backup

---

## Deel 4: Roadmap Integratie

### Voorgestelde Fase 29: LRM & Platform Enhancement

**Weken:** 146-150
**Focus:** Large Reasoning Model integratie + Platform modernisering

#### Week 146-147: LRM Infrastructure

| Component | Beschrijving | Effort |
|-----------|--------------|--------|
| `litellm_gateway.py` | LiteLLM proxy integratie | 8u |
| `provider_registry.py` | Refactor naar LiteLLM | 4u |
| `llm_cost_tracking.py` | Cost tracking per project/tier | 6u |
| Ollama models | Pull deepseek-r1:32b, qwq:32b, qwen3-coder | 2u |
| Tests | Unit + integration tests | 8u |

**Deliverables:**
- LiteLLM gateway operationeel
- 4 nieuwe LRM models beschikbaar
- Cost tracking dashboard

#### Week 148: Agent LRM Upgrade

| Agent | Huidige Model | Nieuwe Model (Reasoning) |
|-------|---------------|-------------------------|
| **Felix** | qwen2.5-coder:7b | qwen3-coder:32b |
| **Quinn** | deepseek-r1 | deepseek-r1:32b-distill |
| **Peter** | deepseek-r1 | qwq:32b |
| **Miguel** | qwen2.5-coder:7b | qwen3-coder:32b |
| **Eliza** | deepseek-r1 | qwq:32b |

**Fallback chain:**
```
Local (Ollama) → Groq (fast) → Claude (premium)
```

#### Week 149: Platform Hosting Setup

| Task | Beschrijving | Effort |
|------|--------------|--------|
| Forgejo deployment | Docker setup, SSL, backup | 8u |
| CI/CD migration | Forgejo Actions workflows | 8u |
| Mirror setup | GitHub ↔ Forgejo sync | 4u |
| Documentation | Hosting procedures | 4u |

#### Week 150: Integration & Testing

| Task | Beschrijving | Effort |
|------|--------------|--------|
| End-to-end testing | Full workflow met LRM agents | 12u |
| Performance benchmark | LRM vs current models | 8u |
| Cost analysis | Real usage metrics | 4u |
| Documentation | Architecture updates | 4u |

### Totale Effort: Fase 29

| Categorie | Uren |
|-----------|------|
| LRM Infrastructure | 28u |
| Agent Upgrade | 16u |
| Platform Hosting | 24u |
| Testing & Docs | 28u |
| **Totaal** | **96u (~2.5 weken)** |

---

## Deel 5: Beslissingsmatrix

### Te Nemen Beslissingen

| # | Beslissing | Opties | Aanbeveling |
|---|------------|--------|-------------|
| **D1** | LRM Provider Strategy | A: Ollama-First, B: Hybrid, C: Full Cloud | **A: Ollama-First** |
| **D2** | Orchestratie Framework | 1: LiteLLM, 2: CrewAI, 3: Minimal | **1: LiteLLM** |
| **D3** | Hosting Platform | A: GitHub only, B: Self-hosted, C: Codeberg, D: Hybrid | **D: Hybrid** |
| **D4** | Fase 29 Prioriteit | High (na Fase 28), Medium, Low | **Medium** |

### Voorgestelde Configuratie

```yaml
# Aanbevolen setup
lrm_strategy: ollama-first
orchestration: litellm
hosting:
  public: github
  private: forgejo-selfhosted
  mirror: codeberg

# Provider tiers (updated)
tier_free:
  - ollama/deepseek-r1:32b-distill
  - ollama/qwq:32b
  - ollama/qwen2.5-coder:32b

tier_basic:
  - groq/qwen3-32b
  - groq/llama-3.1-70b

tier_premium:
  - anthropic/claude-opus-4.5
  - openai/o3-mini
```

---

## Deel 6: Resource Links

### LRM Resources

| Resource | URL |
|----------|-----|
| DeepSeek-R1 | https://github.com/deepseek-ai/DeepSeek-R1 |
| QwQ-32B | https://huggingface.co/Qwen/QwQ-32B |
| Qwen3-Coder | https://github.com/QwenLM/Qwen3-Coder |
| Open-R1 (HF) | https://github.com/huggingface/open-r1 |
| Awesome Deep Reasoning | https://github.com/modelscope/awesome-deep-reasoning |
| Awesome RL for LRMs | https://github.com/TsinghuaC3I/Awesome-RL-for-LRMs |

### Orchestration Resources

| Resource | URL |
|----------|-----|
| LiteLLM | https://github.com/BerriAI/litellm |
| CrewAI | https://github.com/crewAIInc/crewAI |
| LangGraph | https://github.com/langchain-ai/langgraph |
| smolagents | https://github.com/huggingface/smolagents |
| Langroid | https://github.com/langroid/langroid |

### Hosting Resources

| Resource | URL |
|----------|-----|
| Forgejo | https://forgejo.org |
| Gitea | https://gitea.io |
| Codeberg | https://codeberg.org |
| SourceHut | https://sr.ht |
| Awesome Git Hosters | https://github.com/milahu/awesome-git-hosters |

---

## Appendix: Existing Agent-LLM Mapping

### Huidige Configuratie

| Agent | Current Model | Tier |
|-------|---------------|------|
| Felix | qwen2.5-coder:7b | Free |
| Quinn | deepseek-r1 | Free |
| Betty | codellama | Free |
| Eliza | deepseek-r1 | Free |
| Diana | mistral | Free |
| Marcus | qwen2.5-coder:7b | Free |
| Tessa | qwen2.5-coder:7b | Free |
| Miguel | qwen2.5-coder:7b | Free |
| Peter | deepseek-r1 | Free |
| Paul | qwen2.5:7b | Free |
| Vicky | mistral | Free |

### Voorgestelde LRM Upgrade

| Agent | New Primary Model | Reasoning Focus |
|-------|-------------------|-----------------|
| Felix | qwen3-coder:32b | Architecture decisions |
| Quinn | deepseek-r1:32b-distill | Deep code review |
| Betty | codellama:34b | Complex debugging |
| Eliza | qwq:32b | Estimation reasoning |
| Diana | mistral:7b (unchanged) | Documentation |
| Marcus | qwen2.5-coder:32b | Refactoring analysis |
| Tessa | qwen3-coder:32b | Test strategy |
| Miguel | qwen3-coder:32b | Migration planning |
| Peter | qwq:32b | Product decisions |
| Paul | qwq:32b | Sprint planning |
| Vicky | mistral:7b (unchanged) | Design specs |

---

**Document Status:** Research Complete
**Next Action:** Decision required on D1-D4
**Owner:** Team Lead / Architect
