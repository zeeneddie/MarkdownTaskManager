# Deep Extraction Pipeline - Multi-LLM Code Analysis

**Version**: 3.0
**Created**: 2024-12-17
**Updated**: 2024-12-17 (Customer-Selectable Tier Model)
**Status**: PLANNED (Week 81-87)
**Owner**: Architecture Team

---

## Executive Summary

De Deep Extraction Pipeline is een multi-cycle, multi-LLM/LRM systeem voor het extraheren van Epics, Features, User Stories en Tasks uit bestaande codebases. Het systeem biedt **5 customer-selectable tiers** (FREE → PREMIUM) met verschillende LLM configuraties en confidence targets.

**Key Principles**:
- **Customer Choice**: 5 tiers van FREE ($0) tot PREMIUM ($150) per 50K LOC
- **Multi-provider strategie**: 7 providers, 15+ models beschikbaar
- **Re-run Capability**: Upgrade tier en draai extractie opnieuw met delta-tracking
- **Confidence Scaling**: 60% (FREE) → 95% (PREMIUM)
- **Business Model**: Wij betalen ~$0-12, klant betaalt $0-150 (marge 80-92%)

---

## Customer Tier Model

### Pricing Overview

| Tier | Klant Betaalt | Onze Kosten | Marge | Target Confidence | Human Review |
|------|---------------|-------------|-------|-------------------|--------------|
| **FREE** | $0 | ~$0 | N/A | 60% | ❌ |
| **BASIC** | $5 | ~$0.50 | 90% | 70% | ❌ |
| **STANDARD** | $25 | ~$5.00 | 80% | 80% | ❌ |
| **PROFESSIONAL** | $75 | ~$10.00 | 87% | 90% | ✅ Optional |
| **PREMIUM** | $150 | ~$12.00 | 92% | 95% | ✅ Included |

*Prijzen per 50K LOC. Projecten <10K LOC: minimum $5 (excl. FREE)*

### Tier LLM Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER → LLM MAPPING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FREE ($0)                                                                  │
│  ├── Cycle 1: Ollama only (Qwen-Coder, DeepSeek-R1, CodeLlama)            │
│  ├── Cycle 2: Skip                                                         │
│  ├── Cycle 3: Skip                                                         │
│  ├── Cycle 4: No human review                                              │
│  └── Cycle 5: DeepSeek-R1 (local synthesis)                               │
│                                                                             │
│  BASIC ($5)                                                                 │
│  ├── Cycle 1: Ollama + Groq Llama 3.1 + Qwen-Turbo (5 models)             │
│  ├── Cycle 2: Qwen-Plus (1M context, $0.40)                               │
│  ├── Cycle 3: Skip                                                         │
│  ├── Cycle 4: No human review                                              │
│  └── Cycle 5: Qwen-Plus                                                    │
│                                                                             │
│  STANDARD ($25) ★ RECOMMENDED                                               │
│  ├── Cycle 1: Ollama + Gemini Flash-Lite + Qwen-Turbo + Groq (7 models)   │
│  ├── Cycle 2: Gemini 2.5 Flash (1M context)                               │
│  ├── Cycle 3: Gemini 2.5 Pro                                              │
│  ├── Cycle 4: No human review                                              │
│  └── Cycle 5: Gemini 2.5 Pro                                              │
│                                                                             │
│  PROFESSIONAL ($75)                                                         │
│  ├── Cycle 1: Full 7-model parallel                                        │
│  ├── Cycle 2: Gemini 2.5 Flash                                            │
│  ├── Cycle 3: Gemini Pro + GPT-5.2 (dual verification)                    │
│  ├── Cycle 4: Human review (optional, async)                              │
│  └── Cycle 5: Gemini 3 Pro                                                │
│                                                                             │
│  PREMIUM ($150)                                                             │
│  ├── Cycle 1: Full 7-model parallel                                        │
│  ├── Cycle 2: Gemini 2.5 Flash                                            │
│  ├── Cycle 3: Gemini Pro + GPT-5.2 (dual verification)                    │
│  ├── Cycle 4: Human review (included, prioritized)                        │
│  └── Cycle 5: Claude Opus 4.5 (best reasoning)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Re-Run & Upgrade Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTRACTION RE-RUN FLOW                                │
│                                                                             │
│  Initial Run (FREE)                                                         │
│  └── 45K LOC → 23 Epics, 67 Features (60% confidence)                      │
│                     │                                                       │
│                     ▼                                                       │
│  User: "Confidence too low, upgrade to STANDARD"                           │
│                     │                                                       │
│                     ▼                                                       │
│  Re-Run (STANDARD, $25)                                                     │
│  └── Same 45K LOC → 28 Epics (+5), 89 Features (+22) (80% confidence)     │
│                     │                                                       │
│                     ▼                                                       │
│  Delta Report:                                                             │
│  ├── +5 new Epics discovered (business logic gaps)                        │
│  ├── +22 new Features (integration points)                                │
│  ├── 12 Stories reclassified (bug → feature)                              │
│  └── Confidence: 60% → 80% (+20%)                                         │
│                                                                             │
│  User: "Need 95% for compliance, upgrade to PREMIUM"                       │
│                     │                                                       │
│                     ▼                                                       │
│  Re-Run (PREMIUM, $150 - $25 credit = $125)                                │
│  └── Final: 31 Epics, 102 Features, 95% confidence                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Onboarding Tier Selection

De tier selectie wordt geïntegreerd in zowel PROJECT_INTAKE als BROWN_PAPER workflows:

**Step in Workflow:**
```
GREEN_PAPER Workflow:
1. Business Requirements (BMAD 6 questions)
2. Initial Code Scan (estimate LOC)
3. **TIER SELECTION** ← NEW
4. Deep Extraction (tier-specific LLMs)
5. Epic/Feature/Story Generation
6. Review & Refinement

BROWN_PAPER Workflow:
1. Legacy Analysis (BMAD 8 questions)
2. Initial Code Scan (estimate LOC)
3. **TIER SELECTION** ← NEW
4. Deep Extraction (tier-specific LLMs)
5. Migration Plan Generation
6. Review & Refinement
```

---

## 1. LLM Arsenal

### 1.1 Beschikbare LLMs (7 Providers, 15+ Models)

#### Tier 1: FREE (Local Ollama)
| Model | Specialisatie | Context | Use Case |
|-------|---------------|---------|----------|
| qwen2.5-coder:7b | Architecture, patterns | 32K | Structural analysis |
| deepseek-r1 (LRM) | Business logic, reasoning | 128K | Domain extraction |
| codellama | Security, bugs, debt | 16K | Security scan |
| mistral | Documentation, summaries | 32K | Doc mining |

#### Tier 2: ULTRA-CHEAP ($0.05-$0.15/M input)
| Provider | Model | Input/Output | Context | Use Case |
|----------|-------|--------------|---------|----------|
| **Alibaba** | Qwen-Turbo | $0.05/$0.20 | 1M | Bulk code analysis |
| **Google** | Gemini 2.0 Flash-Lite | $0.075/$0.30 | 1M | Fast parallel scan |
| **Google** | Gemini 2.5 Flash-Lite | $0.10/$0.40 | 1M | Agentic tasks |
| **Groq** | Llama 3.1 8B | $0.05/$0.08 | 128K | Speed validation |

#### Tier 3: CHEAP ($0.30-$0.60/M input)
| Provider | Model | Input/Output | Context | Use Case |
|----------|-------|--------------|---------|----------|
| **Google** | Gemini 2.5 Flash | $0.30/$2.50 | 1M | Cross-enrichment |
| **Groq** | Qwen3-32B | $0.29/$0.59 | 128K | Fast reasoning |
| **Alibaba** | Qwen-Plus | $0.40/$1.20 | 1M | Extended analysis |
| **Groq** | Llama 3.3 70B | $0.59/$0.79 | 128K | Deep code review |

#### Tier 4: MID ($1.00-$2.00/M input)
| Provider | Model | Input/Output | Context | Use Case |
|----------|-------|--------------|---------|----------|
| **Moonshot** | Kimi K2 | $1.00/$3.00 | 128K | 1T parameter mega-model |
| **Google** | Gemini 2.5 Pro | $1.25/$10.00 | 1M | Coding + reasoning |
| **OpenAI** | GPT-5.2 | $1.75/$14.00 | 128K | Coding specialist |
| **Google** | Gemini 3 Pro | $2.00/$12.00 | 200K+ | Best agentic/vibe-coding |

#### Tier 5: PREMIUM ($5.00+/M input)
| Provider | Model | Input/Output | Context | Use Case |
|----------|-------|--------------|---------|----------|
| **Anthropic** | Claude Opus 4.5 | $5.00/$25.00 | 200K | Final synthesis + reasoning |

### 1.2 LLM vs LRM Distinction

| Type | Models | Best For |
|------|--------|----------|
| **LLM** (Language Model) | Qwen-Coder, CodeLlama, Gemini Flash, GPT-5.2 | Code scanning, pattern detection, fast analysis |
| **LRM** (Large Reasoning Model) | DeepSeek-R1, Claude Opus 4.5, Gemini 2.5/3 Pro | Synthesis, conflict resolution, complex reasoning |

### 1.3 LLM Rollen in Pipeline (7 Providers)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM ROLE ASSIGNMENT (7 PROVIDERS)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CYCLE 1: INDEPENDENT ANALYSIS (7 models parallel, ~$0.30)                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  [OLLAMA FREE]                                                       │   │
│  │    Qwen-Coder      → Architecture, Patterns, Components             │   │
│  │    DeepSeek-R1     → Business Logic, Domain Rules (LRM)             │   │
│  │    CodeLlama       → Security Issues, Technical Debt, Bugs          │   │
│  │                                                                      │   │
│  │  [PAID - ULTRA-CHEAP]                                                │   │
│  │    Gemini Flash-Lite → Code Structure, API Surface ($0.14)          │   │
│  │    Qwen-Turbo        → Integration Points, Data Models ($0.09)      │   │
│  │    Groq Llama 3.1    → Fast Validation Pass ($0.07)                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CYCLE 2: CROSS-ENRICHMENT (Gemini 2.5 Flash orchestrates, ~$0.68)         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Gemini 2.5 Flash (1M context, $0.30/$2.50):                        │   │
│  │    → Loads ALL Cycle 1 outputs (fits in 1M context!)                │   │
│  │    → Asks each model: "What did others miss?"                       │   │
│  │    → Cross-validates business logic vs technical debt               │   │
│  │    → Identifies gaps between security and architecture views        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CYCLE 3: CONFLICT DETECTION (Gemini Pro + GPT-5.2, ~$4.60)                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Gemini 2.5 Pro ($1.25/$10): "Excels at coding + complex reasoning" │   │
│  │    → Identifies conflicts, scores confidence                        │   │
│  │    → Uses 1M context for full codebase awareness                    │   │
│  │                                                                      │   │
│  │  GPT-5.2 ($1.75/$14): "Coding & agentic specialist"                 │   │
│  │    → Validates Gemini findings, adds code-specific nuance           │   │
│  │    → Output: Consensus + Conflicts + Confidence scores              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CYCLE 4: HUMAN DECISION (Only conflicts, async, $0)                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Dashboard shows ONLY (<20% of items):                              │   │
│  │    - Items with confidence < 80%                                    │   │
│  │    - Items where 7 models disagree                                  │   │
│  │    - Suggested resolutions from each provider                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CYCLE 5: FINAL SYNTHESIS (Claude Opus 4.5 OR Gemini 3 Pro, ~$3-7)         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  OPTION A: Claude Opus 4.5 ($5/$25) - Best reasoning (~$6.50)       │   │
│  │  OPTION B: Gemini 3 Pro ($2/$12) - Best agentic (~$4.80)            │   │
│  │                                                                      │   │
│  │  Final arbiter generates:                                           │   │
│  │    - Final Epic/Feature/Story/Task hierarchy                        │   │
│  │    - Function Point estimates (IFPUG method)                        │   │
│  │    - Risk assessment (via Quinn prompt)                             │   │
│  │    - Implementation roadmap                                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOTAL COST: ~$8.78 (Gemini) to ~$12.08 (Opus) per 50K LOC extraction      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Architecture

### 2.1 High-Level Flow

```
                                    CODE INPUT
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 1: CODE PARSING                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ AST Parser  │  │ Import Map  │  │ Call Graph  │  │ Data Flow   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 2: CHUNKING                                  │
│  Code → Semantic Chunks (max 4000 tokens each)                             │
│  Preserves: class boundaries, function groups, module context              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 3: PARALLEL ANALYSIS                         │
│                                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│   │  Qwen   │    │DeepSeek │    │CodeLlama│    │  Codex  │                │
│   │ Coder   │    │   R1    │    │         │    │   CLI   │                │
│   └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘                │
│        │              │              │              │                      │
│        ▼              ▼              ▼              ▼                      │
│   Architecture    Business      Security       Code                       │
│   Analysis        Logic         Analysis       Structure                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 4: CROSS-ENRICHMENT                          │
│                                                                             │
│   Each LLM reviews another's output and adds missing insights              │
│   Orchestrated by Claude Sonnet                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 5: SYNTHESIS                                 │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    DUAL CONFLICT DETECTION                          │   │
│   │                                                                     │   │
│   │   GPT-4-Turbo ◄─────────────────────────────► Claude Sonnet        │   │
│   │        │                                            │               │   │
│   │        └──────────► CONSENSUS MATRIX ◄──────────────┘               │   │
│   │                           │                                         │   │
│   │                           ▼                                         │   │
│   │              ┌─────────────────────────┐                           │   │
│   │              │ Confidence > 80%: AUTO  │                           │   │
│   │              │ Confidence < 80%: HUMAN │                           │   │
│   │              │ Conflict: HUMAN DECIDE  │                           │   │
│   │              └─────────────────────────┘                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                    ┌─────────────────┐  ┌─────────────────┐
                    │   AUTO-ACCEPT   │  │  HUMAN REVIEW   │
                    │   (80%+ conf)   │  │  (conflicts)    │
                    └────────┬────────┘  └────────┬────────┘
                             │                    │
                             └─────────┬──────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 6: FINAL GENERATION                          │
│                                                                             │
│                         ┌─────────────────┐                                │
│                         │  CLAUDE OPUS    │                                │
│                         │  Final Arbiter  │                                │
│                         └────────┬────────┘                                │
│                                  │                                         │
│                                  ▼                                         │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│   │   EPICS     │  │  FEATURES   │  │   STORIES   │  │    TASKS    │      │
│   │ + FP Total  │  │ + FP/Feature│  │ + FP + SP   │  │ + Hours     │      │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  RISK ANALYSIS  │
                              │  (Quinn Agent)  │
                              └─────────────────┘
```

### 2.2 Database Schema Extensions

```sql
-- New tables for Deep Extraction Pipeline (v3.0 with Tier Support)

-- Add extraction_tier to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS extraction_tier VARCHAR(20) DEFAULT 'FREE';
-- Values: 'FREE', 'BASIC', 'STANDARD', 'PROFESSIONAL', 'PREMIUM'

-- Extraction Sessions (with Tier)
CREATE TABLE extraction_sessions (
    id UUID PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES items(id),
    workflow_type VARCHAR(20) NOT NULL,  -- 'brown_paper' | 'project_intake'
    status VARCHAR(20) DEFAULT 'started',
    current_cycle INTEGER DEFAULT 1,

    -- TIER CONFIGURATION (NEW)
    tier VARCHAR(20) NOT NULL DEFAULT 'FREE',
    tier_price_usd FLOAT,              -- What customer pays
    tier_cost_estimate FLOAT,           -- Our estimated cost
    tier_confidence_target FLOAT,       -- Expected confidence (0.60-0.95)

    -- Input
    source_path VARCHAR(500),
    total_files INTEGER,
    total_lines INTEGER,

    -- Progress
    cycle_1_completed_at TIMESTAMP,
    cycle_2_completed_at TIMESTAMP,
    cycle_3_completed_at TIMESTAMP,
    cycle_4_completed_at TIMESTAMP,  -- Human decisions
    cycle_5_completed_at TIMESTAMP,

    -- Results
    total_epics INTEGER,
    total_features INTEGER,
    total_stories INTEGER,
    total_tasks INTEGER,
    total_function_points FLOAT,

    -- Confidence
    avg_confidence FLOAT,
    items_auto_accepted INTEGER,
    items_human_reviewed INTEGER,

    -- Cost tracking
    total_tokens_used INTEGER,
    actual_cost_usd FLOAT,              -- Renamed: actual vs tier_cost_estimate
    margin_usd FLOAT,                   -- tier_price_usd - actual_cost_usd

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Extraction Runs (for Re-Run Capability) NEW
CREATE TABLE extraction_runs (
    id UUID PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES projects(id),
    session_id UUID REFERENCES extraction_sessions(id),
    run_number INTEGER DEFAULT 1,

    -- Tier for this run
    tier VARCHAR(20) NOT NULL,
    tier_price_usd FLOAT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Link to previous run (for delta calculation)
    previous_run_id UUID REFERENCES extraction_runs(id),

    -- Delta from previous run
    delta_epics INTEGER DEFAULT 0,
    delta_features INTEGER DEFAULT 0,
    delta_stories INTEGER DEFAULT 0,
    delta_tasks INTEGER DEFAULT 0,
    confidence_improvement FLOAT DEFAULT 0,

    -- Cost
    actual_cost_usd FLOAT,
    tokens_used INTEGER,

    -- Credit applied (if upgrade from previous tier)
    credit_from_previous FLOAT DEFAULT 0,
    amount_charged FLOAT,  -- tier_price_usd - credit_from_previous

    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for efficient run history queries
CREATE INDEX ix_extraction_runs_project ON extraction_runs(project_id);
CREATE INDEX ix_extraction_runs_session ON extraction_runs(session_id);

-- LLM Analysis Results (per cycle, per LLM)
CREATE TABLE extraction_llm_results (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES extraction_sessions(id) ON DELETE CASCADE,
    cycle INTEGER NOT NULL,
    llm_provider VARCHAR(50) NOT NULL,  -- 'ollama', 'anthropic', 'openai'
    llm_model VARCHAR(100) NOT NULL,

    -- Analysis type
    analysis_type VARCHAR(50),  -- 'architecture', 'business_logic', 'security', 'code_structure'

    -- Raw output
    raw_output TEXT,
    parsed_output JSONB,

    -- Extracted items
    extracted_epics JSONB DEFAULT '[]',
    extracted_features JSONB DEFAULT '[]',
    extracted_stories JSONB DEFAULT '[]',

    -- Metrics
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    cost_usd FLOAT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Cross-Enrichment Results
CREATE TABLE extraction_enrichments (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES extraction_sessions(id) ON DELETE CASCADE,

    -- Source and reviewer
    source_result_id UUID REFERENCES extraction_llm_results(id),
    reviewer_llm VARCHAR(100),

    -- Enrichment
    additions JSONB DEFAULT '[]',      -- New items found
    modifications JSONB DEFAULT '[]',  -- Suggested changes
    confidence_adjustments JSONB,      -- Per-item confidence changes

    created_at TIMESTAMP DEFAULT NOW()
);

-- Consensus Items
CREATE TABLE extraction_consensus (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES extraction_sessions(id) ON DELETE CASCADE,

    -- Item identification
    item_type VARCHAR(20),  -- 'epic', 'feature', 'story', 'task'
    item_title VARCHAR(300),
    item_description TEXT,

    -- Consensus data
    supporting_llms JSONB,           -- Which LLMs agree
    confidence_score FLOAT,          -- 0-100
    confidence_breakdown JSONB,      -- Per-factor scores

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'auto_accepted', 'human_review', 'accepted', 'rejected'
    human_decision VARCHAR(20),
    human_feedback TEXT,
    decided_at TIMESTAMP,
    decided_by VARCHAR(100),

    -- Final item reference
    final_epic_id UUID,
    final_feature_id UUID,
    final_story_id UUID,
    final_task_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Conflicts requiring human decision
CREATE TABLE extraction_conflicts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES extraction_sessions(id) ON DELETE CASCADE,

    -- Conflict identification
    conflict_type VARCHAR(50),  -- 'scope', 'priority', 'classification', 'existence'
    item_type VARCHAR(20),

    -- Competing interpretations
    option_a JSONB,  -- LLM A's view
    option_b JSONB,  -- LLM B's view
    option_c JSONB,  -- LLM C's view (optional)
    option_d JSONB,  -- LLM D's view (optional)

    -- LLM recommendations
    llm_recommendation VARCHAR(20),  -- 'a', 'b', 'c', 'd', 'merge'
    recommendation_reasoning TEXT,

    -- Human resolution
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'resolved'
    human_choice VARCHAR(20),
    human_reasoning TEXT,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Add function_points to Story model
ALTER TABLE task_stories ADD COLUMN IF NOT EXISTS function_points FLOAT;
ALTER TABLE task_stories ADD COLUMN IF NOT EXISTS fp_complexity VARCHAR(20);
ALTER TABLE task_stories ADD COLUMN IF NOT EXISTS fp_type VARCHAR(20);
ALTER TABLE task_stories ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT;

-- Add function_points to Task model
ALTER TABLE task_tasks ADD COLUMN IF NOT EXISTS function_points FLOAT;
ALTER TABLE task_tasks ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT;

-- Generic Risk Assessment (not just migration)
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS project_id VARCHAR(50);
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS epic_id UUID;
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS extraction_session_id UUID;
CREATE INDEX IF NOT EXISTS ix_risk_project ON risk_assessments(project_id);
```

---

## 3. Cycle Details

### 3.1 Cycle 1: Independent Analysis

**Duration**: ~5-15 minutes (parallel execution)
**LLMs**: Qwen-Coder, DeepSeek-R1, CodeLlama, Codex-CLI
**Cost**: ~$0 (all Ollama/local)

#### Prompt Templates

**Qwen-Coder (Architecture Analysis)**:
```markdown
You are an expert software architect analyzing an existing codebase.

## CODE CONTEXT
{chunked_code}

## YOUR TASK
Analyze this code and extract:

1. **ARCHITECTURAL PATTERNS**
   - Design patterns used (MVC, Repository, Factory, etc.)
   - Layer structure (presentation, business, data)
   - Module boundaries and responsibilities

2. **COMPONENTS**
   For each component, provide:
   - Name
   - Type (service, controller, model, utility, etc.)
   - Responsibilities (3-5 bullet points)
   - Dependencies (what it imports/uses)
   - Dependents (what uses it)

3. **POTENTIAL EPICS**
   Based on the architecture, suggest high-level Epics:
   - Epic title
   - Business capability it represents
   - Components involved
   - Estimated complexity (1-5)

Output as JSON:
{
  "patterns": [...],
  "components": [...],
  "suggested_epics": [...],
  "architectural_concerns": [...]
}
```

**DeepSeek-R1 (Business Logic)**:
```markdown
You are a business analyst reverse-engineering business rules from code.

## CODE CONTEXT
{chunked_code}

## YOUR TASK
Think step by step about the business logic in this code.

<thinking>
1. What business domain does this code serve?
2. What are the key business entities?
3. What business rules are enforced?
4. What workflows/processes are implemented?
</thinking>

Extract:

1. **BUSINESS DOMAINS**
   - Domain name
   - Core entities
   - Business rules (explicit and implicit)

2. **USER WORKFLOWS**
   For each workflow:
   - Workflow name
   - Actor (who performs it)
   - Steps involved
   - Business outcome

3. **POTENTIAL USER STORIES**
   Format: "As a [user], I want [goal] so that [benefit]"
   Include acceptance criteria for each.

Output as JSON:
{
  "domains": [...],
  "workflows": [...],
  "user_stories": [...],
  "business_rules": [...]
}
```

**CodeLlama (Security & Debt)**:
```markdown
You are a security auditor and technical debt assessor.

## CODE CONTEXT
{chunked_code}

## YOUR TASK
Analyze for:

1. **SECURITY ISSUES**
   - Vulnerabilities (OWASP Top 10)
   - Authentication/authorization gaps
   - Data validation issues
   - Hardcoded secrets

2. **TECHNICAL DEBT**
   - Code smells
   - Outdated patterns
   - Missing tests
   - Documentation gaps
   - Deprecated dependencies

3. **MAINTENANCE STORIES**
   For each issue, create a maintenance story:
   - Title
   - Type (security, debt, refactor)
   - Priority (critical, high, medium, low)
   - Estimated effort

Output as JSON:
{
  "security_issues": [...],
  "technical_debt": [...],
  "maintenance_stories": [...],
  "risk_score": 1-10
}
```

**Codex-CLI (Code Structure)**:
```markdown
Analyze this codebase structure:

## CODE CONTEXT
{chunked_code}

## FILE STRUCTURE
{file_tree}

Extract:

1. **API SURFACE**
   - Public endpoints
   - Input/output schemas
   - Authentication requirements

2. **DATA MODELS**
   - Entities and relationships
   - Database schema (if visible)
   - Validation rules

3. **INTEGRATION POINTS**
   - External services called
   - Message queues
   - File I/O

4. **FEATURE BREAKDOWN**
   For each feature area:
   - Feature name
   - Related files
   - Complexity assessment
   - Test coverage status

Output as JSON:
{
  "api_endpoints": [...],
  "data_models": [...],
  "integrations": [...],
  "features": [...]
}
```

### 3.2 Cycle 2: Cross-Enrichment

**Duration**: ~10-20 minutes (sequential)
**Orchestrator**: Claude Sonnet
**Reviewers**: Same 4 Ollama LLMs
**Cost**: ~$0.50-1.00 (Sonnet orchestration)

#### Process

```python
async def run_cross_enrichment(self, cycle1_results: Dict) -> Dict:
    """
    Each LLM reviews another's output and suggests additions.

    Pattern:
    - Qwen reviews DeepSeek's business logic → adds technical context
    - DeepSeek reviews CodeLlama's security → adds business impact
    - CodeLlama reviews Codex's structure → adds security concerns
    - Codex reviews Qwen's architecture → adds implementation details
    """

    enrichment_pairs = [
        ("qwen", "deepseek", "Add technical implementation details to business stories"),
        ("deepseek", "codelama", "Add business impact assessment to security issues"),
        ("codellama", "codex", "Add security considerations to feature breakdown"),
        ("codex", "qwen", "Add implementation specifics to architectural components"),
    ]

    enrichments = []
    for reviewer, reviewee, instruction in enrichment_pairs:
        prompt = f"""
        You are {reviewer}, reviewing {reviewee}'s analysis.

        ## ORIGINAL ANALYSIS BY {reviewee.upper()}
        {cycle1_results[reviewee]}

        ## YOUR EXPERTISE
        {self.get_llm_expertise(reviewer)}

        ## TASK
        {instruction}

        What did {reviewee} miss that you would add?
        What would you modify or clarify?

        Output additions and modifications as JSON.
        """

        result = await self.call_llm(reviewer, prompt)
        enrichments.append(result)

    return enrichments
```

### 3.3 Cycle 3: Conflict Detection

**Duration**: ~5-10 minutes
**LLMs**: GPT-4-Turbo + Claude Sonnet (dual verification)
**Cost**: ~$2-5 (both premium models)

#### Consensus Algorithm

```python
def calculate_consensus(self, all_outputs: List[Dict]) -> ConsensusResult:
    """
    Determine consensus across all LLM outputs.

    Confidence scoring:
    - 4/4 LLMs agree: 95% confidence
    - 3/4 LLMs agree: 80% confidence
    - 2/4 LLMs agree: 50% confidence (conflict)
    - 1/4 LLMs mention: 30% confidence (needs validation)
    """

    # Flatten all extracted items
    all_items = self.flatten_items(all_outputs)

    # Group similar items (fuzzy matching on title + description)
    grouped = self.group_similar_items(all_items, threshold=0.7)

    consensus_items = []
    conflict_items = []

    for group in grouped:
        agreement_count = len(group.sources)

        # Calculate base confidence
        base_confidence = {
            4: 0.95,
            3: 0.80,
            2: 0.50,
            1: 0.30
        }.get(agreement_count, 0.30)

        # Adjust for evidence strength
        evidence_bonus = self.calculate_evidence_strength(group)

        # Adjust for pattern recognition
        pattern_bonus = self.calculate_pattern_match(group)

        final_confidence = min(0.99, base_confidence + evidence_bonus + pattern_bonus)

        item = ConsensusItem(
            title=group.merged_title,
            description=group.merged_description,
            item_type=group.item_type,
            confidence=final_confidence,
            supporting_llms=group.sources,
            variants=group.variants if agreement_count < 4 else None
        )

        if final_confidence >= 0.80:
            consensus_items.append(item)
        else:
            conflict_items.append(item)

    return ConsensusResult(
        consensus=consensus_items,
        conflicts=conflict_items,
        stats={
            "total_items": len(grouped),
            "auto_accepted": len(consensus_items),
            "needs_review": len(conflict_items),
            "avg_confidence": sum(i.confidence for i in consensus_items) / len(consensus_items)
        }
    )
```

### 3.4 Cycle 4: Human Decision

**Duration**: Async (hours to days)
**Interface**: Web Dashboard
**Involvement**: Only conflicts + final approval

#### Dashboard Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXTRACTION REVIEW DASHBOARD                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Project: legacy-crm-system          Status: Awaiting Review               │
│  Extraction: 2024-12-17 14:30        Confidence: 87% average               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SUMMARY                                                             │   │
│  │                                                                     │   │
│  │  ✅ Auto-Accepted:  142 items (confidence > 80%)                   │   │
│  │  ⚠️ Needs Review:    23 items (confidence 50-80%)                  │   │
│  │  ❓ Conflicts:        8 items (LLMs disagree)                      │   │
│  │                                                                     │   │
│  │  [View Auto-Accepted] [Review Required Items] [Resolve Conflicts]  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CONFLICTS TO RESOLVE (8)                                           │   │
│  │                                                                     │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │ CONFLICT #1: Epic Classification                              │ │   │
│  │  │                                                               │ │   │
│  │  │ Should "User Authentication" be:                              │ │   │
│  │  │                                                               │ │   │
│  │  │ ○ Option A (Qwen): Separate Epic "Security & Auth"           │ │   │
│  │  │   Reasoning: Authentication is complex enough for own epic    │ │   │
│  │  │                                                               │ │   │
│  │  │ ○ Option B (DeepSeek): Feature under "User Management" Epic  │ │   │
│  │  │   Reasoning: Auth is part of user lifecycle                   │ │   │
│  │  │                                                               │ │   │
│  │  │ ○ Option C (Codex): Split - Login=Feature, MFA=Epic          │ │   │
│  │  │   Reasoning: MFA complexity warrants separation               │ │   │
│  │  │                                                               │ │   │
│  │  │ LLM Recommendation: Option A (Security patterns detected)     │ │   │
│  │  │                                                               │ │   │
│  │  │ Your Decision: [A] [B] [C] [Custom...]                       │ │   │
│  │  │ Notes: ________________________________________               │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  [Previous] [Skip for now] [Next]                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Save Progress]                              [Submit All Decisions]       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Cycle 5: Final Synthesis

**Duration**: ~10-20 minutes
**LLM**: Claude Opus (highest quality)
**Cost**: ~$5-15

#### Final Synthesis Prompt

```markdown
You are the final arbiter creating a complete project breakdown from multiple AI analyses.

## CONTEXT
Project: {project_name}
Type: {workflow_type}  # 'existing_project' or 'migration'
Total code files: {file_count}
Total lines: {line_count}

## CONSENSUS ITEMS (Auto-Accepted, 80%+ confidence)
{consensus_items_json}

## HUMAN DECISIONS ON CONFLICTS
{resolved_conflicts_json}

## ORIGINAL CODE STRUCTURE
{code_structure_summary}

## YOUR TASK

Create the FINAL, AUTHORITATIVE breakdown:

### 1. EPIC HIERARCHY
For each Epic:
- ID: EPIC-001, EPIC-002, etc.
- Title
- Description (2-3 sentences)
- Business Value
- Estimated Total FP (IFPUG method)
- Risk Level (low/medium/high)
- Dependencies on other Epics

### 2. FEATURE BREAKDOWN
For each Feature within Epics:
- ID: FEAT-001-001 (Epic-Feature)
- Title
- Description
- Technical Approach
- Estimated FP
- Complexity (simple/moderate/complex)

### 3. USER STORIES
For each Story within Features:
- ID: STORY-001-001-001
- Title (As a... I want... so that...)
- Description
- Acceptance Criteria (Given/When/Then format)
- Function Points (IFPUG)
- Story Points (Fibonacci: 1,2,3,5,8,13)
- Priority (critical/high/medium/low)

### 4. TECHNICAL TASKS
For each Task within Stories:
- ID: TASK-001-001-001-001
- Title
- Type (backend/frontend/database/testing/devops)
- Estimated Hours
- Dependencies

### 5. RISK REGISTER
- RISK-001: Title, Probability(1-5), Impact(1-5), Mitigation

### 6. FUNCTION POINT SUMMARY
- Total Adjusted FP
- FP by Epic
- FP by Complexity
- Recommended Team Size
- Estimated Duration (weeks)

Output as structured JSON following the schema below:
{output_schema}
```

---

## 4. Cost Model (7 Providers)

### 4.1 Per-Extraction Cost Estimate (50K LOC Codebase)

| Cycle | Models Used | Tokens | Cost | Notes |
|-------|-------------|--------|------|-------|
| **1** | 3x Ollama + Gemini Flash-Lite + Qwen-Turbo + Groq | 1M in / 200K out | **$0.30** | 7 parallel perspectives |
| **2** | Gemini 2.5 Flash | 600K in / 200K out | **$0.68** | 1M context = full analysis |
| **3** | Gemini 2.5 Pro + GPT-5.2 | 400K in / 100K out | **$4.60** | Dual-verification |
| **4** | Human Review | - | **$0.00** | <20% of items |
| **5A** | Claude Opus 4.5 | 300K in / 200K out | **$6.50** | Best reasoning |
| **5B** | Gemini 3 Pro | 300K in / 200K out | **$4.80** | Best agentic |

#### Total Cost Options

| Option | Final Synthesizer | Total Cost | Cost per 10K LOC |
|--------|-------------------|------------|------------------|
| **Budget** | Gemini 3 Pro | **~$10.38** | ~$2.08 |
| **Premium** | Claude Opus 4.5 | **~$12.08** | ~$2.42 |

### 4.2 Cost Comparison vs Alternatives

| Approach | Cost per 50K LOC | Confidence | Speed |
|----------|------------------|------------|-------|
| Manual extraction (developer) | $2,000-5,000 | 70-85% | 2-4 weeks |
| Single LLM (GPT-4) | ~$50-100 | 50-70% | 30 min |
| Dual LLM (Claude + GPT) | ~$30-60 | 65-80% | 45 min |
| **Our 7-Provider Pipeline** | **~$10-12** | **90-95%** | **20-30 min** |

### 4.3 Provider Cost Breakdown

| Provider | Role in Pipeline | Cost Contribution | % of Total |
|----------|------------------|-------------------|------------|
| **Ollama** | Cycle 1 bulk (3 models) | $0.00 | 0% |
| **Groq** | Cycle 1 validation | $0.07 | <1% |
| **Alibaba** | Cycle 1 integration | $0.09 | <1% |
| **Google** (Flash-Lite) | Cycle 1 structure | $0.14 | 1% |
| **Google** (Flash) | Cycle 2 orchestration | $0.68 | 6% |
| **Google** (Pro) | Cycle 3 reasoning | $2.38 | 20% |
| **OpenAI** (GPT-5.2) | Cycle 3 coding | $2.22 | 18% |
| **Anthropic** (Opus) | Cycle 5 synthesis | $6.50 | 54% |

### 4.4 Cost Optimization Strategies

1. **Cache intermediate results** - Don't re-run Cycle 1 if code hasn't changed
2. **Batch similar projects** - Share learnings across extractions
3. **Confidence threshold tuning** - Higher threshold = more auto-accept = less premium LLM use
4. **Ollama scaling** - Run multiple Ollama instances for parallelism
5. **Use Gemini 3 Pro for final** - Save ~$1.70 per extraction with minimal quality loss
6. **Context caching** - Gemini has $0.03-$0.25 caching, reuse for same codebase
7. **Groq for speed** - 394-840 TPS makes Cycle 1 validation nearly instant

---

## 5. Implementation Plan

### Week 81-82: Foundation

**Goals**:
- [ ] Database migrations for new tables
- [ ] `DeepExtractionService` skeleton
- [ ] Cycle 1 implementation (4 Ollama parallel)
- [ ] Basic chunking and parsing

**Deliverables**:
- Migration 036: extraction tables
- `backend/app/services/deep_extraction_service.py`
- `backend/app/services/code_chunking_service.py`

### Week 83-84: Cross-Enrichment & Synthesis

**Goals**:
- [ ] Cycle 2 implementation (cross-enrichment)
- [ ] Cycle 3 implementation (conflict detection)
- [ ] Consensus algorithm
- [ ] GPT-4 and OpenAI integration

**Deliverables**:
- `backend/app/services/extraction_council_service.py`
- `backend/app/services/consensus_scoring_service.py`
- `backend/app/providers/openai_provider.py`

### Week 85: Human Review UI

**Goals**:
- [ ] Conflict resolution dashboard
- [ ] Review queue management
- [ ] Decision tracking

**Deliverables**:
- `frontend/extraction-review.html`
- `backend/app/api/extraction_review.py`

### Week 86: Final Synthesis & Integration

**Goals**:
- [ ] Cycle 5 implementation (Opus synthesis)
- [ ] FP estimation integration (Eliza)
- [ ] Risk analysis integration (Quinn)
- [ ] Story/Task model updates

**Deliverables**:
- Migration 037: FP fields on Story/Task
- Integration with existing hierarchy models

### Week 87: Testing & Documentation

**Goals**:
- [ ] End-to-end testing with real codebases
- [ ] Performance optimization
- [ ] Documentation
- [ ] Prompt refinement based on results

---

## 6. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extraction Confidence | >85% average | Consensus score |
| Human Review Rate | <20% of items | Items requiring decision |
| FP Accuracy | +/-15% vs manual | Compare to expert estimate |
| Time to Extract | <30 min for 50K LOC | Wall clock time |
| Cost per Extraction | <$15 | Total LLM costs |
| Story Completeness | >90% coverage | Manual audit sample |

---

## 7. Integration Points

### 7.1 Existing Services

| Service | Integration |
|---------|-------------|
| `brown_paper_service.py` | Calls DeepExtraction instead of simple scan |
| `project_registration_service.py` | Triggers DeepExtraction after registration |
| `task_generation_service.py` | Receives hierarchy from DeepExtraction |
| `llm_council_service.py` | Reuse consensus patterns |
| `fp_estimation_service.py` | Called in Cycle 5 for FP |

### 7.2 New API Endpoints

```
POST   /api/extraction/start           Start extraction for project
GET    /api/extraction/{id}/status     Get extraction progress
GET    /api/extraction/{id}/consensus  Get auto-accepted items
GET    /api/extraction/{id}/conflicts  Get items needing review
POST   /api/extraction/{id}/resolve    Submit human decisions
POST   /api/extraction/{id}/finalize   Trigger Cycle 5
GET    /api/extraction/{id}/result     Get final hierarchy
```

---

## 8. Appendix: Full Prompt Library

See: `backend/app/prompts/extraction/`
- `cycle1_architecture.md`
- `cycle1_business_logic.md`
- `cycle1_security.md`
- `cycle1_code_structure.md`
- `cycle2_enrichment.md`
- `cycle3_conflict_detection.md`
- `cycle5_final_synthesis.md`
