# ROADMAP: Geplande Weken (Week 80-90+)

> **DEPRECATED:** This file is archived. See:
> - [phases-completed.md](phases-completed.md) - for completed phases (Fase 1-19)
> - [phases-current.md](phases-current.md) - for current work (Week 127)
> - [phases-planned.md](phases-planned.md) - for planned work (Fase 20+)

**Project:** MarQed AI Agent Software Platform
**Periode:** 2025-12-18 (Week 80) - 2026-08-31 (Week 90+)
**Status:** ARCHIVED (most content now in phases-completed.md)

---

## Quick Overview

| Tier/Fase | Weken | Focus | Components | Status |
|-----------|-------|-------|------------|--------|
| **Tier 4: Security** | 80-82 | Security Agents | GhostCrew, ShadowGraph | 🚀 IN PROGRESS (~95%) |
| **Fase 10: Deep Extraction** | 81-87 | Customer-Selectable Tier Model | 5-cycle pipeline, 7 providers, 5 tiers (FREE→PREMIUM) | 📋 PLANNED |
| **Fase 11: Tool-Workflow** | 88-90 | Ontbrekende integraties | Graph, CodeWiki, CCPM, BigAGI | 📋 PLANNED |
| **Fase 12: GitHub/DevOps** | 91-92 | Repository Intelligence | GitHub + Azure DevOps integration | 📋 PLANNED |

**Business Model:** [docs/BUSINESS_MODEL.md](../BUSINESS_MODEL.md)

### Customer Tier Model (Week 81-87)

| Tier | Klant Betaalt | Confidence | LLMs | Human Review |
|------|---------------|------------|------|--------------|
| **FREE** | $0 | 60% | 3 (Ollama) | ❌ |
| **BASIC** | $5 | 70% | 5 | ❌ |
| **STANDARD** ★ | $25 | 80% | 7 | ❌ |
| **PROFESSIONAL** | $75 | 90% | 9 | Optional |
| **PREMIUM** | $150 | 95% | 10 | Included |

*Per 50K LOC. ★ Recommended. Re-run capability with tier upgrade.*

---

## Week 80-82: GhostCrew Security (Tier 4)

**Status:** ~90% Complete
**Doel:** Multi-agent security scanning system

### Components

| Component | Lines | Tests | Status |
|-----------|-------|-------|--------|
| **GhostCrewService** | 850 | 45 | ✅ DONE |
| **GhostCrew API** (19 endpoints) | 600 | 35 | ✅ DONE |
| **ShadowGraph Service** | 400 | 20 | ✅ DONE |
| **Migration 035** | 150 | - | ✅ DONE |
| **GhostCrew Dashboard** | 500 | - | ✅ DONE |
| **E2E Tests** | - | 31 | ✅ DONE |
| **Total** | **2,500** | **131** | **~90%** |

### GhostCrew Features
- 3 Security Agents: security_agent, audit_agent, compliance_agent
- Quick Scan mode (pattern-based)
- Full Crew Scan mode (multi-agent)
- Assist Mode (OWASP/CWE lookups)
- ShadowGraph integration
- Real-time dashboard

### Remaining Tasks (Week 82)
- [ ] Workflow integration testing
- [ ] Documentation finalization
- [ ] Performance optimization

---

## Week 81-87: Deep Extraction Pipeline (Fase 10)

**Doel:** Customer-selectable tier model met 60-95% extractie confidence
**Business Model:** We betalen ~$0-12, klant betaalt $0-150 per 50K LOC (80-92% marge)
**Specification:** [docs/architecture/deep-extraction-pipeline.md](../architecture/deep-extraction-pipeline.md)

### Problem Statement

Huidige gaps in BROWN_PAPER en PROJECT_INTAKE workflows:
- Single-pass LLM analysis mist context
- Geen cross-validation tussen LLMs
- Function Points alleen op Epic niveau (niet Story/Task)
- Risk Assessment alleen voor Migration (niet algemeen)
- Extraction confidence ~60% (target: 95%)
- **Geen customer choice in kwaliteit vs prijs**

### Solution: Customer-Selectable Tiers

| Tier | Price | Our Cost | Margin | Confidence | Key Features |
|------|-------|----------|--------|------------|--------------|
| **FREE** | $0 | ~$0 | N/A | 60% | 3 local LLMs, basic extraction |
| **BASIC** | $5 | ~$0.50 | 90% | 70% | +Groq/Qwen fast scan |
| **STANDARD** ★ | $25 | ~$5.00 | 80% | 80% | +Gemini cross-validation |
| **PROFESSIONAL** | $75 | ~$10.00 | 87% | 90% | +GPT-5.2, optional human review |
| **PREMIUM** | $150 | ~$12.00 | 92% | 95% | +Claude Opus, included human review |

**Re-Run Capability:** Customer kan upgraden naar hogere tier en opnieuw runnen. Systeem toont delta (Epics +5, Confidence +20%).

### 5-Cycle Architecture

```
CYCLE 1 ─► CYCLE 2 ─► CYCLE 3 ─► CYCLE 4 ─► CYCLE 5
Independent  Cross-     Conflict   Human      Final
Analysis    Enrichment  Detection  Decision   Synthesis
(4 Ollama)  (Sonnet)   (Haiku)    (UI)       (Opus)
```

### Week-by-Week Planning

#### Week 81: Database Schema + Tier Foundation + FREE Tier
**Effort:** 28 uur
**Focus:** Tier infrastructure, FREE tier volledig werkend

**Database Tables (Tier-Aware):**
```sql
-- Projects table uitbreiding
ALTER TABLE projects ADD COLUMN IF NOT EXISTS extraction_tier VARCHAR(20) DEFAULT 'FREE';

-- Extraction session tracking (met tier)
CREATE TABLE extraction_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    codebase_path VARCHAR(500) NOT NULL,
    workflow_type VARCHAR(50) NOT NULL,  -- 'BROWN_PAPER', 'PROJECT_INTAKE'
    tier VARCHAR(20) NOT NULL DEFAULT 'FREE',  -- NEW: customer tier
    status VARCHAR(50) DEFAULT 'created',
    total_files_analyzed INTEGER,
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Individual LLM extraction results
CREATE TABLE extraction_llm_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES extraction_sessions(id),
    cycle_number INTEGER NOT NULL,  -- 1-5
    llm_provider VARCHAR(50) NOT NULL,
    llm_model VARCHAR(100) NOT NULL,
    extraction_type VARCHAR(50) NOT NULL,  -- 'architecture', 'business_logic', 'security', 'structure'
    extracted_items JSONB NOT NULL,
    confidence_score FLOAT,
    tokens_used INTEGER,
    cost_usd FLOAT DEFAULT 0,  -- NEW: cost tracking
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Re-run tracking (NEW)
CREATE TABLE extraction_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    tier VARCHAR(20) NOT NULL,
    previous_run_id UUID REFERENCES extraction_runs(id),
    delta_epics INTEGER DEFAULT 0,
    delta_features INTEGER DEFAULT 0,
    delta_stories INTEGER DEFAULT 0,
    confidence_improvement FLOAT DEFAULT 0,
    credit_from_previous FLOAT DEFAULT 0,
    amount_charged FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consensus results per extraction type
CREATE TABLE extraction_consensus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES extraction_sessions(id),
    extraction_type VARCHAR(50) NOT NULL,
    agreement_percentage FLOAT NOT NULL,
    agreed_items JSONB NOT NULL,
    conflicting_items JSONB,
    human_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conflicts requiring human decision
CREATE TABLE extraction_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consensus_id UUID REFERENCES extraction_consensus(id),
    item_type VARCHAR(50) NOT NULL,
    llm_opinions JSONB NOT NULL,
    human_decision VARCHAR(50),
    human_notes TEXT,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100)
);
```

**Tier Configuration:**
```python
TIER_CONFIG = {
    "FREE": {
        "price": 0,
        "target_confidence": 0.60,
        "llms": ["ollama/qwen-coder", "ollama/deepseek-r1", "ollama/codellama"],
        "cycles": [1, 5],  # Skip 2,3,4
        "human_review": False
    }
}
```

**FREE Tier Implementatie:**
- Alleen Ollama LLMs (qwen-coder, deepseek-r1, codellama)
- Cycle 1 (parallel analysis) + Cycle 5 (synthesis met deepseek-r1)
- Target: 60% confidence
- Zero external cost

**Deliverables:**
- [ ] Migration 036_add_extraction_tables.py (tier-aware)
- [ ] `TierAwareExtractionService` scaffold
- [ ] TIER_CONFIG datastructure
- [ ] FREE tier volledig werkend
- [ ] Unit tests: 15+

---

#### Week 82: Cycle 1 + FREE/BASIC Tiers Complete
**Effort:** 32 uur
**Focus:** BASIC tier implementatie, Cycle 1 tier-aware

**Tier → LLM Mapping (Cycle 1):**

| Tier | LLMs (Parallel) | Provider Mix | Estimated Cost |
|------|-----------------|--------------|----------------|
| **FREE** | 3 | 100% Ollama | $0 |
| **BASIC** | 5 | Ollama + Groq + Qwen | ~$0.30 |

**BASIC Tier Config:**
```python
TIER_CONFIG["BASIC"] = {
    "price": 5,
    "target_confidence": 0.70,
    "llms": [
        "ollama/qwen-coder", "ollama/deepseek-r1", "ollama/codellama",  # FREE base
        "groq/llama-3.1-8b",  # Fast, cheap external validation
        "alibaba/qwen-turbo"  # Additional perspective
    ],
    "cycles": [1, 5],  # Still skip 2,3,4
    "human_review": False
}
```

**LLM Assignments (BASIC Tier - Parallel):**

| LLM | Provider | Focus | Cost/50K |
|-----|----------|-------|----------|
| qwen2.5-coder:7b | Ollama | Architecture | $0 |
| deepseek-r1 | Ollama | Business Logic | $0 |
| codellama | Ollama | Security/Debt | $0 |
| llama-3.1-8b | Groq | Structure validation | ~$0.07 |
| qwen-turbo | Alibaba | Cross-check | ~$0.09 |

**Extraction Prompts:** (unchanged)

```python
ARCHITECTURE_PROMPT = """
Analyze this codebase and extract:
1. EPICS: Major functional areas (auth, payments, reporting, etc.)
2. FEATURES: Distinct capabilities within each epic
3. Architectural patterns used
4. Module boundaries and responsibilities

Output JSON:
{
    "epics": [{"id": "E1", "name": "...", "description": "...", "confidence": 0.9}],
    "features": [{"id": "F1", "epic_id": "E1", "name": "...", "description": "...", "confidence": 0.85}],
    "patterns": ["MVC", "Repository", ...],
    "modules": [{"name": "...", "responsibility": "..."}]
}
"""
```

**Tier Routing Service:**
```python
class TierAwareExtractionService:
    async def get_cycle1_llms(self, tier: str) -> List[LLMConfig]:
        """Return LLMs for Cycle 1 based on customer tier."""
        return TIER_CONFIG[tier]["llms"]

    async def should_run_cycle(self, tier: str, cycle: int) -> bool:
        """Check if tier includes this cycle."""
        return cycle in TIER_CONFIG[tier]["cycles"]
```

**Deliverables:**
- [ ] BASIC tier configuratie
- [ ] Tier routing in Cycle 1
- [ ] Groq provider integration
- [ ] Alibaba/Qwen provider integration
- [ ] Cost tracking per LLM call
- [ ] Unit tests: 20+

---

#### Week 83: Cycle 2 + STANDARD Tier ★
**Effort:** 28 uur
**Focus:** STANDARD tier (recommended), Gemini cross-validation

**STANDARD Tier Config:** (★ Recommended)
```python
TIER_CONFIG["STANDARD"] = {
    "price": 25,
    "target_confidence": 0.80,
    "llms": {
        "cycle_1": [
            "ollama/qwen-coder", "ollama/deepseek-r1", "ollama/codellama",
            "groq/llama-3.1-8b", "alibaba/qwen-turbo",
            "google/gemini-2.0-flash-lite", "google/gemini-2.5-flash"  # NEW
        ],
        "cycle_2": "google/gemini-2.5-flash"  # Cross-enrichment
    },
    "cycles": [1, 2, 5],  # Skip 3,4
    "human_review": False
}
```

**Tier Comparison (Cycle 2):**

| Tier | Cycle 2 | Cross-Enrichment By | Cost Added |
|------|---------|---------------------|------------|
| FREE | ❌ Skip | - | $0 |
| BASIC | ❌ Skip | - | $0 |
| **STANDARD** | ✅ Run | Gemini 2.5 Flash ($0.30/$2.50) | ~$0.68 |
| PROFESSIONAL | ✅ Run | Gemini 2.5 Flash | ~$0.68 |
| PREMIUM | ✅ Run | Gemini 2.5 Flash | ~$0.68 |

**Process:**
1. Collect 5-7 independent analyses from Cycle 1
2. Gemini 2.5 Flash receives combined input
3. Identifies gaps, inconsistencies, missing items
4. Produces enriched extraction with adjusted confidence

**Cross-Enrichment Prompt:**

```python
CROSS_ENRICHMENT_PROMPT = """
You have received {num_llms} independent code analyses from different LLMs:

=== ARCHITECTURE ANALYSIS (qwen2.5-coder) ===
{architecture_results}

=== BUSINESS LOGIC ANALYSIS (deepseek-r1) ===
{business_results}

=== SECURITY/DEBT ANALYSIS (codellama) ===
{security_results}

=== STRUCTURE ANALYSIS (groq/llama) ===
{structure_results}

=== VALIDATION (qwen-turbo) ===
{validation_results}

{additional_results}

Your task:
1. Identify items mentioned by multiple LLMs (high confidence)
2. Find gaps - items likely missing from any analysis
3. Resolve inconsistencies between analyses
4. Add details from one analysis to enrich another
5. Flag items with conflicting interpretations

Output enriched JSON with confidence scores adjusted based on cross-validation.
"""
```

**Deliverables:**
- [ ] STANDARD tier configuratie
- [ ] Gemini 2.5 Flash integration
- [ ] Cycle 2 conditional execution (tier-aware)
- [ ] Cross-enrichment prompts
- [ ] Confidence adjustment logic
- [ ] Unit tests: 15+

---

#### Week 84: Cycle 3 + PROFESSIONAL Tier
**Effort:** 28 uur
**Focus:** PROFESSIONAL tier, dual-model conflict detection

**PROFESSIONAL Tier Config:**
```python
TIER_CONFIG["PROFESSIONAL"] = {
    "price": 75,
    "target_confidence": 0.90,
    "llms": {
        "cycle_1": [
            "ollama/qwen-coder", "ollama/deepseek-r1", "ollama/codellama",
            "groq/llama-3.1-8b", "alibaba/qwen-turbo",
            "google/gemini-2.0-flash-lite", "google/gemini-2.5-flash",
            "openai/gpt-5.2", "moonshot/kimi-k2"  # NEW
        ],
        "cycle_2": "google/gemini-2.5-flash",
        "cycle_3": ["google/gemini-2.5-pro", "openai/gpt-5.2"]  # Dual conflict detection
    },
    "cycles": [1, 2, 3, 5],  # Skip only 4 (optional human)
    "human_review": "optional"  # Customer choice
}
```

**Tier Comparison (Cycle 3):**

| Tier | Cycle 3 | Conflict Detection | Cost Added |
|------|---------|-------------------|------------|
| FREE | ❌ Skip | - | $0 |
| BASIC | ❌ Skip | - | $0 |
| STANDARD | ❌ Skip | - | $0 |
| **PROFESSIONAL** | ✅ Run | Gemini Pro + GPT-5.2 (dual) | ~$4.60 |
| PREMIUM | ✅ Run | Gemini Pro + GPT-5.2 (dual) | ~$4.60 |

**Consensus Rules:**
- **80%+ agreement** → Auto-accept
- **60-79% agreement** → Flag for review, suggest majority
- **<60% agreement** → Require human decision (PROFESSIONAL/PREMIUM only)

**Dual-Model Conflict Detection:**
```python
async def cycle3_conflict_detection(tier: str, enriched_results: dict):
    if tier not in ["PROFESSIONAL", "PREMIUM"]:
        # Lower tiers: simple consensus from Cycle 1/2
        return simple_consensus(enriched_results)

    # PROFESSIONAL/PREMIUM: Dual LRM validation
    gemini_opinion = await gemini_pro.analyze(enriched_results)
    gpt_opinion = await gpt_5_2.analyze(enriched_results)

    return {
        "high_confidence": items_both_agree(gemini_opinion, gpt_opinion),
        "review_needed": items_one_disagrees(gemini_opinion, gpt_opinion),
        "conflicts": items_both_disagree(gemini_opinion, gpt_opinion)
    }
```

**Conflict Types:**
- **Naming conflicts**: Same thing, different names
- **Scope conflicts**: Different epic/feature boundaries
- **Priority conflicts**: Different importance assessment
- **Missing conflicts**: One LLM found it, others didn't

**Deliverables:**
- [ ] PROFESSIONAL tier configuratie
- [ ] Gemini 2.5 Pro integration
- [ ] GPT-5.2 integration
- [ ] Dual-model conflict detection
- [ ] Consensus calculation (tier-aware)
- [ ] Human review toggle (optional for PROFESSIONAL)
- [ ] Unit tests: 20+

---

#### Week 85: Cycle 4 + Re-Run Capability
**Effort:** 28 uur
**Focus:** Human review (PROFESSIONAL/PREMIUM), tier upgrade flow

**Human Review per Tier:**

| Tier | Cycle 4 (Human) | Behavior |
|------|-----------------|----------|
| FREE | ❌ Skip | No conflicts shown |
| BASIC | ❌ Skip | No conflicts shown |
| STANDARD | ❌ Skip | Auto-resolve conflicts |
| **PROFESSIONAL** | ⚪ Optional | Customer can enable |
| **PREMIUM** | ✅ Included | Always available |

**Re-Run & Upgrade Flow:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  EXTRACTION RESULTS - Project: HCI-CRS                              │
├─────────────────────────────────────────────────────────────────────┤
│  Current Tier: BASIC ($5)          Confidence: 68%                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EXTRACTED:                                                         │
│  • 12 Epics identified                                             │
│  • 45 Features extracted                                           │
│  • 89 Stories generated                                            │
│  • 156 Tasks created                                               │
│                                                                     │
│  ⚠️ Confidence below target. Consider upgrading tier.              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  UPGRADE OPTIONS                                            │   │
│  │                                                             │   │
│  │  ○ STANDARD ($25)  - Expected: +12% confidence, +8 epics    │   │
│  │    Credit from BASIC: $5 → You pay: $20                     │   │
│  │                                                             │   │
│  │  ○ PROFESSIONAL ($75) - Expected: +22% confidence, +15 epics│   │
│  │    Credit from BASIC: $5 → You pay: $70                     │   │
│  │    + Optional human review                                  │   │
│  │                                                             │   │
│  │  ○ PREMIUM ($150) - Expected: +27% confidence, +20 epics    │   │
│  │    Credit from BASIC: $5 → You pay: $145                    │   │
│  │    + Included human review + Claude Opus synthesis          │   │
│  │                                                             │   │
│  │  [Upgrade & Re-Run] [Keep Current Results]                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Re-Run API:**
```python
@router.post("/api/extraction/{project_id}/upgrade")
async def upgrade_and_rerun(
    project_id: int,
    new_tier: str,
    db: Session = Depends(get_db)
):
    """
    Upgrade tier and re-run extraction.
    - Calculate credit from previous run
    - Charge difference only
    - Store delta for comparison
    """
    previous_run = get_latest_run(project_id)
    credit = previous_run.amount_charged if previous_run else 0
    new_price = TIER_CONFIG[new_tier]["price"]
    amount_due = max(0, new_price - credit)

    new_run = await run_extraction(project_id, new_tier)

    return {
        "run_id": new_run.id,
        "tier": new_tier,
        "credit_applied": credit,
        "amount_charged": amount_due,
        "delta": calculate_delta(previous_run, new_run)
    }
```

**Delta Tracking:**
```python
def calculate_delta(prev: ExtractionRun, curr: ExtractionRun) -> dict:
    return {
        "epics": curr.total_epics - prev.total_epics,
        "features": curr.total_features - prev.total_features,
        "stories": curr.total_stories - prev.total_stories,
        "confidence_improvement": curr.confidence - prev.confidence,
        "additional_items": get_new_items(prev, curr)
    }
```

**Deliverables:**
- [ ] Re-run upgrade API endpoint
- [ ] Credit calculation service
- [ ] Delta tracking and comparison
- [ ] Upgrade suggestion algorithm
- [ ] Human review dashboard (human-review-extraction.html)
- [ ] Decision persistence
- [ ] Unit tests: 25+

---

#### Week 86: Cycle 5 + PREMIUM Tier
**Effort:** 28 uur
**Focus:** PREMIUM tier met Claude Opus synthesis

**PREMIUM Tier Config:**
```python
TIER_CONFIG["PREMIUM"] = {
    "price": 150,
    "target_confidence": 0.95,
    "llms": {
        "cycle_1": [
            "ollama/qwen-coder", "ollama/deepseek-r1", "ollama/codellama",
            "groq/llama-3.1-8b", "alibaba/qwen-turbo",
            "google/gemini-2.0-flash-lite", "google/gemini-2.5-flash",
            "openai/gpt-5.2", "moonshot/kimi-k2",
            "anthropic/claude-haiku"  # NEW: 10th LLM
        ],
        "cycle_2": "google/gemini-2.5-flash",
        "cycle_3": ["google/gemini-2.5-pro", "openai/gpt-5.2"],
        "cycle_5": "anthropic/claude-opus-4.5"  # Premium synthesizer
    },
    "cycles": [1, 2, 3, 4, 5],  # All cycles
    "human_review": True  # Included
}
```

**Cycle 5 Synthesizer per Tier:**

| Tier | Cycle 5 | Synthesizer | Cost |
|------|---------|-------------|------|
| FREE | ✅ Run | Ollama DeepSeek-R1 | $0 |
| BASIC | ✅ Run | Ollama DeepSeek-R1 | $0 |
| STANDARD | ✅ Run | Ollama DeepSeek-R1 | $0 |
| PROFESSIONAL | ✅ Run | Gemini 3 Pro ($2/$12) | ~$4.80 |
| **PREMIUM** | ✅ Run | Claude Opus 4.5 ($5/$25) | ~$6.50 |

**Claude Opus 4.5 Synthesis (PREMIUM only):**
1. Receives: Auto-accepted items + Human decisions
2. Generates: Complete Epic → Feature → Story → Task hierarchy
3. Adds: Function Point estimates (IFPUG) per Story/Task
4. Adds: Story Point estimates (PERT) per Story
5. Adds: Risk Assessment per Epic/Feature
6. Adds: **Confidence explanations** (why this extraction is reliable)

**Tier-Aware Function Point Estimation:**

```python
async def estimate_story_function_points(story: dict, tier: str) -> FPEstimate:
    """
    IFPUG Function Point estimation - detail varies by tier.
    """
    if tier == "FREE":
        return {"fp_estimate": "N/A", "reason": "Upgrade to BASIC for estimates"}

    if tier == "BASIC":
        return basic_fp_estimate(story)  # Simple heuristic

    if tier in ["STANDARD", "PROFESSIONAL"]:
        return standard_fp_estimate(story)  # IFPUG-based

    # PREMIUM: Full IFPUG with Opus validation
    estimate = await opus_validated_fp_estimate(story)
    return {
        "unadjusted_fp": estimate.ufp,
        "complexity_factors": estimate.factors,
        "adjusted_fp": estimate.afp,
        "effort_hours": fp_to_hours(estimate.afp),
        "confidence": 0.95,
        "opus_validation": estimate.explanation
    }
```

**Final Output Structure:** (PREMIUM tier)

```json
{
    "project": "HCI-CRS Migration",
    "tier": "PREMIUM",
    "extraction_confidence": 0.94,
    "cost_breakdown": {
        "cycle_1": "$0.30",
        "cycle_2": "$0.68",
        "cycle_3": "$4.60",
        "cycle_4": "included",
        "cycle_5": "$6.50",
        "total": "$12.08"
    },
    "hierarchy": {
        "epics": [
            {
                "id": "E001",
                "name": "User Authentication System",
                "description": "Complete user auth with SSO and MFA",
                "total_fp": 45,
                "total_sp": 89,
                "risk_level": "MEDIUM",
                "confidence_explanation": "High confidence: 8/10 LLMs agreed on scope...",
                "features": [...]
            }
        ]
    }
}
```

**Deliverables:**
- [ ] PREMIUM tier configuratie
- [ ] Claude Opus 4.5 integration
- [ ] Tier-aware synthesis service
- [ ] IFPUG FP calculator (tier-aware)
- [ ] Risk assessment integration
- [ ] Confidence explanation generation
- [ ] Final hierarchy generator
- [ ] Export to project.md format
- [ ] Unit tests: 20+

---

#### Week 87: Integration + Tier Selection UI
**Effort:** 28 uur
**Focus:** Onboarding tier picker, pricing page, workflow integration

**Onboarding Tier Selection:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  PROJECT ONBOARDING - Step 3: Select Extraction Tier               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Choose your extraction quality level:                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ○ FREE ($0)                                                   │ │
│  │   • 60% confidence target                                     │ │
│  │   • 3 local LLMs (Ollama)                                    │ │
│  │   • Basic Epic/Feature extraction                            │ │
│  │   • No Function Point estimates                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ○ BASIC ($5)                                                  │ │
│  │   • 70% confidence target                                     │ │
│  │   • 5 LLMs (Ollama + Groq + Qwen)                            │ │
│  │   • Improved extraction with cross-validation                │ │
│  │   • Basic FP estimates                                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ● STANDARD ($25) ★ RECOMMENDED                                │ │
│  │   • 80% confidence target                                     │ │
│  │   • 7 LLMs including Gemini cross-enrichment                 │ │
│  │   • Full Epic → Feature → Story → Task hierarchy             │ │
│  │   • IFPUG-based Function Point estimates                     │ │
│  │   BEST VALUE for most projects                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ○ PROFESSIONAL ($75)                                          │ │
│  │   • 90% confidence target                                     │ │
│  │   • 9 LLMs with dual-model conflict detection                │ │
│  │   • Optional human review for edge cases                     │ │
│  │   • Full IFPUG + risk assessment                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ○ PREMIUM ($150)                                              │ │
│  │   • 95% confidence target (highest)                          │ │
│  │   • 10 LLMs + Claude Opus synthesis                          │ │
│  │   • Included human review                                    │ │
│  │   • Confidence explanations per extraction                   │ │
│  │   For mission-critical projects                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  💡 You can upgrade and re-run later. Credit from previous tier   │
│     will be applied to the upgrade.                                │
│                                                                     │
│  [Continue with STANDARD] [Compare Tiers]                          │
└─────────────────────────────────────────────────────────────────────┘
```

**New Frontend Components:**
- `tier-selector.html` - Onboarding tier picker
- `tier-comparison.html` - Side-by-side tier comparison
- `extraction-results.html` - Results with upgrade options
- `pricing-page.html` - Public pricing information

**Workflow Integration:**

1. **BROWN_PAPER workflow update:**
   - Question 1-4: Use Deep Extraction (tier-aware)
   - Auto-populate BMAD answers from extraction
   - Risk assessment from LLM consensus
   - Show tier upgrade suggestions if confidence < target

2. **PROJECT_INTAKE workflow update:**
   - Tier selection during onboarding (Step 3)
   - Replace single-LLM scan with tier-based extraction
   - Store selected tier in project record

**Testing:**
- E2E tests for full tier flow
- Tier upgrade scenarios
- Re-run with delta tracking
- Performance benchmarks per tier
- Cost validation per tier

**Deliverables:**
- [ ] Tier selector component (tier-selector.html)
- [ ] Tier comparison page (tier-comparison.html)
- [ ] Pricing page (pricing-page.html)
- [ ] Onboarding flow integration
- [ ] BROWN_PAPER tier awareness
- [ ] PROJECT_INTAKE tier selection
- [ ] E2E test suite (30+ tests)
- [ ] Documentation update
- [ ] Unit tests: 20+

---

### Cost Model (7 Providers, 15+ Models)

**Per 50K LOC Extraction:**

| Cycle | Provider(s) | Model(s) | Tokens | Cost |
|-------|-------------|----------|--------|------|
| 1 | Ollama (FREE) | Qwen-Coder, DeepSeek-R1, CodeLlama | 1M in / 200K out | $0.00 |
| 1 | Google | Gemini 2.0 Flash-Lite ($0.075/$0.30) | 100K | $0.14 |
| 1 | Alibaba | Qwen-Turbo ($0.05/$0.20) | 100K | $0.09 |
| 1 | Groq | Llama 3.1 8B ($0.05/$0.08) | 100K | $0.07 |
| 2 | Google | Gemini 2.5 Flash ($0.30/$2.50) | 600K in / 200K out | $0.68 |
| 3 | Google | Gemini 2.5 Pro ($1.25/$10) | 200K in / 50K out | $2.38 |
| 3 | OpenAI | GPT-5.2 ($1.75/$14) | 200K in / 50K out | $2.22 |
| 4 | Human | Review <20% conflicts | - | $0.00 |
| 5A | Anthropic | Claude Opus 4.5 ($5/$25) | 300K in / 200K out | $6.50 |
| 5B | Google | Gemini 3 Pro ($2/$12) | 300K in / 200K out | $4.80 |

| Option | Final Synthesizer | Total Cost | vs Manual |
|--------|-------------------|------------|-----------|
| **Budget** | Gemini 3 Pro | **~$10.38** | 99.5% cheaper |
| **Premium** | Claude Opus 4.5 | **~$12.08** | 99.4% cheaper |

*Comparison: Manual extraction costs $2,000-5,000 per 50K LOC*

### Success Metrics

| Metric | Before | Target | Measured By |
|--------|--------|--------|-------------|
| Extraction confidence (PREMIUM) | 60% | 95% | LLM agreement + human validation |
| FP coverage | Epic only | Story/Task | IFPUG compliance |
| Human effort | 4h review | 30m review | Time tracking |
| Items extracted | ~50% | ~95% | Manual sampling |
| **Tier adoption** | N/A | 60% paid | % projects on BASIC+ |
| **Tier upgrade rate** | N/A | 30% | FREE→paid conversion |
| **Re-run usage** | N/A | 20% | Projects that re-run extraction |
| **Avg margin** | N/A | 85% | (Revenue - Cost) / Revenue |

### Confidence per Tier (Target)

| Tier | Target Confidence | Actual (Week 87) |
|------|-------------------|------------------|
| FREE | 60% | TBD |
| BASIC | 70% | TBD |
| STANDARD | 80% | TBD |
| PROFESSIONAL | 90% | TBD |
| PREMIUM | 95% | TBD |

---

## Week 88-90: Tool-Workflow Integration (Fase 11)

**Doel:** Alle 11 workflows voorzien van optimale tool-integraties

### Analyse: Ontbrekende Integraties

#### Per Tool (Impact Ranking)

| # | Tool | Ontbreekt in | Priority |
|---|------|--------------|----------|
| 1 | **Graph Persistence** | 8 workflows | HIGH |
| 2 | **CodeWiki** | 6 workflows | HIGH |
| 3 | **CCPM Worktrees** | 5 workflows | MEDIUM |
| 4 | **GhostCrew** | 4 workflows | MEDIUM |
| 5 | **BigAGI Beam** | 3 workflows | LOW |
| 6 | **Layered Analysis** | 2 workflows | LOW |

#### Per Workflow (Gap Analysis)

| Workflow | Geïntegreerd | Ontbrekend | Gap % |
|----------|--------------|------------|-------|
| **ENHANCEMENT** | 0 | 6 | 100% |
| **QUALITY_IMPROVEMENT** | 1 | 5 | 83% |
| **TESTING** | 1 | 5 | 83% |
| **PROJECT_DEFINITION** | 1 | 3 | 75% |
| **BUG** | 2 | 4 | 67% |
| **MAINTENANCE** | 2 | 4 | 67% |
| **NEW_FEATURE** | 2 | 4 | 67% |
| **BROWN_PAPER** | 3 | 3 | 50% |
| **MIGRATION** | 3 | 3 | 50% |
| **GREEN_PAPER** | 2 | 2 | 50% |
| **QUALITY_AUDIT** | 3 | 1 | 25% |

---

### Week 88: Graph Persistence + CodeWiki Integration

**Impact:** 8 workflows verbeterd (Graph) + 6 workflows verbeterd (CodeWiki)
**Effort:** 32 uur

#### Implementatie

```python
# WorkflowToolIntegrationService uitbreidingen

# NEW_FEATURE, MAINTENANCE
async def graph_impact_analysis(project_id: int, changes: List[str]) -> ImpactReport:
    """Analyze impact of code changes on dependency graph."""

# BUG, MIGRATION
async def graph_dependency_check(entity_id: str) -> DependencyReport:
    """Check dependencies for affected entity."""

# QUALITY_AUDIT, QUALITY_IMPROVEMENT
async def graph_coupling_metrics(project_id: int) -> CouplingMetrics:
    """Calculate module coupling and cohesion metrics."""

# TESTING
async def graph_test_coverage_map(project_id: int) -> CoverageMap:
    """Map test files to source files via graph."""

# ENHANCEMENT
async def graph_enhancement_scope(feature_id: str) -> ScopeReport:
    """Determine enhancement scope via graph analysis."""
```

#### Workflows Aangepast
- NEW_FEATURE: Impact analysis voor nieuwe code
- BUG: Dependency tracking voor root cause
- MAINTENANCE: Refactoring impact assessment
- MIGRATION: Cross-module dependency mapping
- QUALITY_AUDIT: Coupling/cohesion metrics
- QUALITY_IMPROVEMENT: Improvement prioritization
- TESTING: Test-to-source mapping
- ENHANCEMENT: Scope determination

---

### Week 89: CCPM Worktrees Uitbreiding

**Impact:** 5 workflows verbeterd
**Effort:** 16 uur

#### Implementatie

```python
# WorkflowToolIntegrationService uitbreidingen

# NEW_FEATURE
async def ccpm_create_feature_branch(feature_id: str) -> Worktree:
    """Create isolated worktree for feature development."""

# BUG
async def ccpm_create_bugfix_branch(bug_id: str) -> Worktree:
    """Create isolated worktree for bug investigation."""

# MAINTENANCE
async def ccpm_parallel_refactor(task_id: str) -> Worktree:
    """Create worktree for parallel refactoring work."""

# TESTING
async def ccpm_test_isolation(test_suite: str) -> Worktree:
    """Create isolated environment for test execution."""

# PROJECT_DEFINITION
async def ccpm_project_scaffold(project_id: int) -> Worktree:
    """Create project scaffold in new worktree."""
```

#### Workflows Aangepast
- NEW_FEATURE: Isolated development environment
- BUG: Safe debugging workspace
- MAINTENANCE: Parallel refactoring branches
- TESTING: Isolated test execution
- PROJECT_DEFINITION: Project scaffolding

---

### Week 90: GhostCrew + BigAGI Uitbreiding

**Impact:** 7 workflows verbeterd
**Effort:** 20 uur

#### GhostCrew Uitbreiding

```python
# GREEN_PAPER
async def ghostcrew_greenfield_audit(project_spec: dict) -> SecurityReport:
    """Security review for new project architecture."""

# TESTING
async def ghostcrew_test_security(test_files: List[str]) -> SecurityTestReport:
    """Security scan of test files and fixtures."""

# ENHANCEMENT
async def ghostcrew_enhancement_scan(diff: str) -> EnhancementSecurityReport:
    """Security scan for enhancement changes."""

# QUALITY_IMPROVEMENT
async def ghostcrew_quality_security(project_id: int) -> QualitySecurityReport:
    """Combined quality + security analysis."""
```

#### BigAGI Uitbreiding

```python
# GREEN_PAPER
async def bigagi_validate_architecture(architecture_doc: str) -> ValidationReport:
    """Multi-model validation of architecture decisions."""

# BROWN_PAPER
async def bigagi_validate_migration_plan(plan: dict) -> ValidationReport:
    """Multi-model consensus on migration strategy."""

# NEW_FEATURE
async def bigagi_validate_feature_design(design: dict) -> ValidationReport:
    """Multi-model validation of feature design."""
```

---

## Tool-Workflow Matrix (Target State)

### Na Week 90

| Workflow | Claude-Mem | CCPM | BigAGI | GhostCrew | Graph | CodeWiki | Layered |
|----------|:----------:|:----:|:------:|:---------:|:-----:|:--------:|:-------:|
| GREEN_PAPER | ✅ | ✅ | ✅ | ✅ | - | - | - |
| BROWN_PAPER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| NEW_FEATURE | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| BUG | ✅ | ✅ | - | ✅ | ✅ | - | - |
| MAINTENANCE | ✅ | ✅ | - | ✅ | ✅ | ✅ | - |
| MIGRATION | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| QUALITY_AUDIT | ✅ | - | ✅ | ✅ | ✅ | - | - |
| QUALITY_IMPROVEMENT | ✅ | - | ✅ | ✅ | ✅ | - | - |
| TESTING | ✅ | ✅ | - | ✅ | ✅ | ✅ | - |
| ENHANCEMENT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| PROJECT_DEFINITION | ✅ | ✅ | ✅ | - | - | - | - |

**Legenda:**
- ✅ = Geïntegreerd
- `-` = Niet van toepassing

---

## Expected Impact

| Metric | Before (Week 82) | After (Week 87) | After (Week 90) | Change |
|--------|------------------|-----------------|-----------------|--------|
| Workflows met tools | 9/11 | 11/11 | 11/11 | +22% |
| Avg tools per workflow | 2.1 | 3.5 | 4.2 | +100% |
| ENHANCEMENT coverage | 0% | 80% | 100% | +100% |
| Graph integration | 3/11 | 8/11 | 11/11 | +267% |
| CodeWiki integration | 0/11 | 4/11 | 6/11 | +600% |
| **Extraction confidence** | 60% | **95%** | 95% | +58% |
| **FP Story/Task coverage** | 0% | **100%** | 100% | NEW |
| **Human review time** | 4h | **30m** | 30m | -87.5% |

---

## Week 91-92: GitHub/DevOps Analysis (Fase 12)

**Doel:** Repository metadata analyse voor verbeterde extraction en project intelligence
**Impact:** BROWN_PAPER, MIGRATION, PROJECT_INTAKE workflows significant verbeterd
**Pricing:** Add-on service $10-$50 per repository

### Problem Statement

Code-only analyse mist cruciale context:
- Commit history toont hot spots en change frequency
- PR history onthult review patterns en merge conflicts
- Issues/bugs correleren met technische schuld
- CI/CD pipelines tonen build complexity
- Team structure identificeert knowledge silos

### Week 91: GitHub Integration

**Effort:** 32 uur
**Focus:** GitHub API integration, repository analysis

#### Features

```python
# GitHubAnalysisService
class GitHubAnalysisService:
    async def analyze_repository(
        self,
        repo_url: str,
        access_token: str,
        depth: Literal["quick", "full"] = "quick"
    ) -> GitHubAnalysisResult:
        """
        Analyze GitHub repository for extraction enrichment.
        """
        return {
            "repository_metrics": await self._get_repo_metrics(repo_url),
            "commit_analysis": await self._analyze_commits(repo_url, depth),
            "pr_analysis": await self._analyze_pull_requests(repo_url, depth),
            "issue_analysis": await self._analyze_issues(repo_url),
            "hot_spots": await self._identify_hot_spots(repo_url),
            "team_analysis": await self._analyze_contributors(repo_url),
            "suggested_epics": await self._suggest_epics_from_issues(repo_url)
        }
```

#### API Endpoints

```
POST /api/github/analyze
POST /api/github/connect
GET  /api/github/repositories
GET  /api/github/repository/{repo}/metrics
GET  /api/github/repository/{repo}/hot-spots
GET  /api/github/repository/{repo}/team
POST /api/github/repository/{repo}/correlate-extraction
```

#### Data Model

```sql
CREATE TABLE github_analyses (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    repo_url VARCHAR(500) NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,  -- 'quick', 'full'
    total_commits INTEGER,
    total_prs INTEGER,
    total_issues INTEGER,
    active_contributors INTEGER,
    hot_spots JSONB,
    team_analysis JSONB,
    suggested_epics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE github_hot_spots (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES github_analyses(id),
    file_path VARCHAR(500) NOT NULL,
    change_count INTEGER,
    bug_correlation_count INTEGER,
    last_modified TIMESTAMP,
    complexity_score FLOAT
);
```

#### Deliverables
- [ ] GitHub API integration service
- [ ] Repository metrics collection
- [ ] Hot spot identification algorithm
- [ ] Issue-to-Epic correlation
- [ ] Team/contributor analysis
- [ ] Migration 037_add_github_analysis_tables.py
- [ ] Unit tests: 25+

---

### Week 92: Azure DevOps Integration + Extraction Correlation

**Effort:** 32 uur
**Focus:** Azure DevOps integration, extraction correlation

#### Features

```python
# AzureDevOpsAnalysisService
class AzureDevOpsAnalysisService:
    async def analyze_project(
        self,
        organization: str,
        project: str,
        pat_token: str,
        include_pipelines: bool = True,
        include_boards: bool = True
    ) -> AzureDevOpsAnalysisResult:
        """
        Analyze Azure DevOps project for extraction enrichment.
        """
        return {
            "repository_metrics": await self._get_repo_metrics(),
            "pipeline_analysis": await self._analyze_pipelines(),
            "board_analysis": await self._analyze_boards(),
            "work_items": await self._get_work_items(),
            "sprint_history": await self._get_sprint_history()
        }
```

#### Extraction Correlation

```python
# ExtractionCorrelationService
class ExtractionCorrelationService:
    async def correlate_with_github(
        self,
        extraction_id: UUID,
        github_analysis_id: UUID
    ) -> CorrelatedExtraction:
        """
        Enrich extraction results with GitHub insights.
        """
        extraction = await self.get_extraction(extraction_id)
        github = await self.get_github_analysis(github_analysis_id)

        return {
            "enriched_epics": self._correlate_epics_with_issues(
                extraction.epics,
                github.suggested_epics
            ),
            "prioritized_features": self._prioritize_by_hot_spots(
                extraction.features,
                github.hot_spots
            ),
            "risk_assessment": self._assess_risk_from_team(
                extraction.epics,
                github.team_analysis
            ),
            "tech_debt_correlation": self._correlate_tech_debt(
                extraction.tech_debt,
                github.issue_analysis
            )
        }
```

#### API Endpoints

```
POST /api/devops/analyze
POST /api/devops/connect
GET  /api/devops/projects
GET  /api/devops/project/{project}/metrics
GET  /api/devops/project/{project}/pipelines
GET  /api/devops/project/{project}/boards
POST /api/extraction/{id}/correlate-github
POST /api/extraction/{id}/correlate-devops
GET  /api/extraction/{id}/enriched
```

#### Pricing Add-on

| Service | Base Price | Per 1000 Commits | Per 100 PRs | Per 100 Issues |
|---------|------------|------------------|-------------|----------------|
| GitHub Quick | $10 | +$2 | +$1 | +$0.50 |
| GitHub Full | $25 | +$5 | +$2 | +$1.00 |
| Azure DevOps Quick | $15 | +$2 | +$1 | +$0.50 |
| Azure DevOps Full | $35 | +$5 | +$2 | +$1.00 |

#### Deliverables
- [ ] Azure DevOps API integration
- [ ] Pipeline analysis service
- [ ] Board/Work Item analysis
- [ ] Extraction correlation service
- [ ] Enriched extraction output
- [ ] Pricing calculation for add-ons
- [ ] Unit tests: 25+
- [ ] E2E tests: 10+

---

### Integration with Deep Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│  ENHANCED EXTRACTION FLOW (with GitHub/DevOps)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STEP 0: Repository Analysis (Optional Add-on)                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ GitHub/DevOps Analysis                                        │ │
│  │ • Commit frequency & hot spots                               │ │
│  │ • PR review patterns                                         │ │
│  │ • Issue correlation                                          │ │
│  │ • Team structure & knowledge silos                           │ │
│  │ • CI/CD pipeline complexity                                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                           ↓                                        │
│  STEP 1-5: Standard Deep Extraction                                │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Cycle 1 → Cycle 2 → Cycle 3 → Cycle 4 → Cycle 5              │ │
│  │ (enriched with repository context)                           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                           ↓                                        │
│  STEP 6: Correlation & Enrichment                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Match extracted Epics with GitHub Issues                   │ │
│  │ • Prioritize Features by hot spot frequency                  │ │
│  │ • Add risk scores based on team analysis                     │ │
│  │ • Correlate tech debt with issue history                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                           ↓                                        │
│  OUTPUT: Enriched Extraction with Repository Intelligence          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Week 111-113: Multi-Language Business Rule Extractors (NEXT PRIORITY)

**Status:** PLANNED
**Specification:** [multi-language-business-rule-extractors.md](../architecture/multi-language-business-rule-extractors.md)
**Origin:** HCI-CRS Agenda Analysis (2025-12-25)

### Problem Statement
Bestaande `BusinessRuleExtractor` ondersteunt alleen Python (AST-based). HCI-CRS analyse toonde:
- 564 business rules in 2 VB.NET/ASP bestanden
- Bestaande extractor vond: **0 regels**

---

### 🔥 HYBRID EXTRACTION ARCHITECTURE

De oplossing is een **3-Tier Hybrid Strategy** die de beste methode per situatie selecteert:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID BUSINESS RULE EXTRACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 1: AST-BASED (Hoogste precisie, waar beschikbaar)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Python      → Python AST (bestaand)                    confidence: 95% ││
│  │ C#          → Roslyn Compiler API                      confidence: 95% ││
│  │ JavaScript  → @babel/parser of tree-sitter             confidence: 90% ││
│  │ TypeScript  → TypeScript Compiler API                  confidence: 90% ││
│  │ Java        → JavaParser                               confidence: 90% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                          ↓ Fallback als geen AST beschikbaar                │
│  TIER 2: REGEX-ENHANCED (Legacy talen, pattern-based)                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ VB.NET       → Regex + Sub/Function/Class detection    confidence: 80% ││
│  │ Classic ASP  → Regex + VBScript structure tracking     confidence: 75% ││
│  │ VBScript     → Regex patterns                          confidence: 70% ││
│  │ T-SQL        → Regex + statement boundaries            confidence: 80% ││
│  │ PL/SQL       → Regex + block detection                 confidence: 80% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                          ↓ Optional enhancement (tier-afhankelijk)          │
│  TIER 3: LLM-ASSISTED (Complex/ambiguous cases)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Ambiguous patterns  → Ollama classification            confidence: 85% ││
│  │ Natural language    → Gemini extraction                confidence: 80% ││
│  │ Cross-validation    → Multi-LLM consensus              confidence: 90% ││
│  │ Premium synthesis   → Claude Opus final pass           confidence: 95% ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  OUTPUT: Unified BusinessRule format met confidence + extraction_method     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Customer Tier vs Extraction Tier Mapping

| Customer Tier | Price | AST (Tier 1) | Regex (Tier 2) | LLM (Tier 3) | Expected Confidence |
|---------------|-------|--------------|----------------|--------------|---------------------|
| **FREE** | $0 | ✅ | ✅ | ❌ | 70-80% |
| **BASIC** | $5 | ✅ | ✅ | Ollama only | 75-85% |
| **STANDARD** ★ | $25 | ✅ | ✅ | + Groq/Gemini | 80-90% |
| **PROFESSIONAL** | $75 | ✅ | ✅ | + GPT-5.2 | 85-92% |
| **PREMIUM** | $150 | ✅ | ✅ | + Claude Opus | 90-95% |

*Alle tiers krijgen AST + Regex. LLM-validatie escaleert per tier.*

---

### Week 111: Phase 1 - Hybrid Core Architecture (24 uur)

| Task | Uren | Output | Tier |
|------|------|--------|------|
| Abstract `BaseBusinessRuleExtractor` with tier support | 4 | `base_extractor.py` | Core |
| `ExtractionTier` enum + `ExtractionResult` dataclass | 2 | `models.py` | Core |
| `VBNetBusinessRuleExtractor` (regex-enhanced) | 6 | `.vb`, `.aspx.vb` support | Tier 2 |
| `ClassicASPExtractor` (regex-enhanced) | 4 | `.asp`, `.asa` support | Tier 2 |
| `ExtractorFactory` with auto-detection + tier selection | 4 | Factory pattern | Core |
| Unit tests + HCI-CRS validation | 4 | `test_extractors.py` | - |

**Deliverables:**
- [ ] `app/services/static_analysis/extractors/base_extractor.py`
- [ ] `app/services/static_analysis/extractors/models.py` (ExtractionTier, ExtractionResult)
- [ ] `app/services/static_analysis/extractors/vbnet_extractor.py`
- [ ] `app/services/static_analysis/extractors/asp_extractor.py`
- [ ] `app/services/static_analysis/extractors/factory.py`
- [ ] Tests: HCI-CRS Agenda detecteert 500+ rules (vs huidige 0)

**Extraction Result Model:**
```python
@dataclass
class ExtractionResult:
    rules: List[BusinessRule]
    extraction_tier: ExtractionTier  # AST, REGEX, LLM_ASSISTED
    extraction_method: str           # "python_ast", "vbnet_regex", "ollama_classification"
    confidence: float                # 0.0-1.0
    processing_time_ms: int
    llm_tokens_used: int = 0         # For cost tracking
```

### Week 111-112: Phase 2 - Stored Procedure Support (16 uur)

| Task | Uren | Output | Tier |
|------|------|--------|------|
| `TSQLExtractor` (SQL Server) | 6 | T-SQL IF/CASE/TRY-CATCH patterns | Tier 2 |
| `PLSQLExtractor` (Oracle) | 4 | PL/SQL IF/CASE/EXCEPTION patterns | Tier 2 |
| Procedure dependency graph | 4 | Call graph between procedures | Tier 2 |
| Tests | 2 | `test_stored_procedures.py` | - |

**Detection Patterns:**
```sql
-- T-SQL
IF @status = 'ACTIVE' BEGIN ... END
CASE WHEN @amount > 1000 THEN 'LARGE' ELSE 'SMALL' END
TRY ... CATCH (error handling)

-- PL/SQL
IF condition THEN ... END IF;
CASE expression WHEN ... THEN ... END CASE;
EXCEPTION WHEN ... THEN ... (error handling)
```

### Week 112: Phase 2.5 - LLM-Assisted Extraction (20 uur) ⭐ NEW

**Doel:** Tier 3 extraction voor ambiguous cases en cross-validation

| Task | Uren | Output | Customer Tier |
|------|------|--------|---------------|
| `LLMRuleClassifier` service | 6 | Classify ambiguous regex matches | BASIC+ |
| `LLMRuleExtractor` service | 6 | Extract rules from natural language comments | STANDARD+ |
| `MultiLLMValidator` service | 4 | Cross-validate with multiple LLMs | PROFESSIONAL+ |
| Tier-aware extraction orchestrator | 2 | Route to appropriate LLMs per tier | All |
| Tests | 2 | `test_llm_extraction.py` | - |

**Deliverables:**
- [ ] `app/services/static_analysis/extractors/llm_classifier.py`
- [ ] `app/services/static_analysis/extractors/llm_extractor.py`
- [ ] `app/services/static_analysis/extractors/multi_llm_validator.py`
- [ ] `app/services/static_analysis/extractors/tier_orchestrator.py`

**LLM Provider Mapping per Customer Tier:**
```python
TIER_LLM_MAPPING = {
    CustomerTier.FREE: [],                    # No LLM assistance
    CustomerTier.BASIC: ["ollama"],           # Local LLMs only
    CustomerTier.STANDARD: ["ollama", "groq", "gemini"],
    CustomerTier.PROFESSIONAL: ["ollama", "groq", "gemini", "openai"],
    CustomerTier.PREMIUM: ["ollama", "groq", "gemini", "openai", "anthropic"],
}
```

**Use Cases voor LLM-Assisted Extraction:**
1. **Ambiguous Regex Match** - Regex vindt `If condition Then` maar LLM bepaalt of het echte business rule is
2. **Comment Extraction** - `' Check if user has permission to edit` → BR-xxx authorization rule
3. **Natural Language in Code** - VBScript met Nederlandse teksten in MsgBox calls
4. **Cross-Validation** - 3 LLMs moeten het eens zijn voor confidence boost

**Example Flow:**
```
                    ┌─────────────────────────────────────────┐
                    │          EXTRACTION ORCHESTRATOR         │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │     1. AST Extraction (if supported)     │
                    │        → Python, C#, JS, TS, Java        │
                    │        confidence: 90-95%                │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │     2. Regex Extraction (fallback)       │
                    │        → VB.NET, ASP, SQL                │
                    │        confidence: 70-80%                │
                    └────────────────────┬────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │ Customer Tier >= BASIC?     │                             │
           │                             ▼                             │
           │              ┌──────────────────────────┐                 │
           │              │  3. LLM Classification    │                 │
           │              │     → Validate regex      │                 │
           │              │     → Boost confidence    │                 │
           │              │     confidence: +5-15%    │                 │
           │              └──────────────────────────┘                 │
           │                             │                             │
           │ Customer Tier >= STANDARD?  │                             │
           │                             ▼                             │
           │              ┌──────────────────────────┐                 │
           │              │  4. Cross-Validation      │                 │
           │              │     → 3 LLMs consensus    │                 │
           │              │     confidence: +10%      │                 │
           │              └──────────────────────────┘                 │
           │                             │                             │
           └─────────────────────────────┼─────────────────────────────┘
                                         ▼
                    ┌────────────────────────────────────────┐
                    │         FINAL EXTRACTION RESULT         │
                    │   rules + confidence + method + cost    │
                    └────────────────────────────────────────┘
```

### Week 112: Phase 3 - Business Rule Correlation (24 uur)

| Task | Uren | Output |
|------|------|--------|
| Entity detection from rules | 4 | "Afspraak", "Client", "Hulpverlener" |
| Call graph builder | 6 | Function → function dependencies |
| `BusinessRuleCorrelator` | 8 | Group rules into workflows |
| Mermaid diagram generator | 4 | Visual workflow representation |
| Tests | 2 | `test_correlation.py` |

**Example Output - Workflow Detection:**
```yaml
workflow: "Afspraak Plannen"
trigger: "User clicks 'Nieuwe Afspraak'"
entities: [Afspraak, Hulpverlener, Client]
steps:
  - type: authorization
    rules: [BR-001, BR-002]
    check: "Mag ik in deze agenda plannen?"
  - type: scheduling
    rules: [BR-015, BR-016]
    check: "Is tijdslot geldig en beschikbaar?"
  - type: data_access
    rules: [BR-042]
    action: "INSERT INTO taAfspraak"
success: "Afspraak gepland"
failures: ["Geen rechten", "Tijdslot bezet"]
```

### Week 112-113: Phase 4 - Integration (16 uur)

| Task | Uren | Output |
|------|------|--------|
| API endpoints | 4 | `/api/business-rules/*` |
| Database models + migration | 2 | `business_rules`, `rule_workflows` tables |
| Frontend dashboard | 6 | `business-rules-dashboard.html` |
| Workflow viewer (Mermaid) | 4 | Interactive workflow diagrams |

**New API Endpoints:**
```
POST /api/business-rules/extract
     Body: { project_id, path, languages: ["vbnet", "asp", "sql"] }

GET  /api/business-rules/{project_id}
GET  /api/business-rules/{project_id}/by-type/{type}

POST /api/business-rules/correlate
     Body: { project_id, strategy: "entity|callgraph" }

GET  /api/workflows/{project_id}
GET  /api/workflows/{id}/diagram
```

### Success Metrics

| Metric | Huidige Waarde | Target Week 113 |
|--------|----------------|-----------------|
| VB.NET rule detection | 0% | 90%+ |
| Classic ASP rule detection | 0% | 85%+ |
| Stored procedure detection | N/A | 80%+ |
| Workflow correlation accuracy | N/A | 75%+ |
| False positive rate | N/A | <15% |

**Hybrid Extraction Metrics (per tier):**

| Customer Tier | Target Confidence | Max Processing Time | Cost per 50K LOC |
|---------------|-------------------|---------------------|------------------|
| FREE | 70-75% | 30 sec | $0 |
| BASIC | 75-80% | 45 sec | <$0.50 |
| STANDARD | 80-85% | 60 sec | <$5.00 |
| PROFESSIONAL | 85-90% | 90 sec | <$10.00 |
| PREMIUM | 90-95% | 120 sec | <$15.00 |

### Week 113: Phase 4.5 - Traceability Implementation (12 uur) ⭐ NEW

**Doel:** Business rules traceerbaar maken naar epic/feature/story hiërarchie

| Task | Uren | Output |
|------|------|--------|
| Database tabellen + migratie | 3 | `epics`, `features`, `user_stories`, `story_business_rules` |
| API endpoints | 4 | CRUD voor traceability, matrix export |
| Traceability views | 2 | `v_traceability_matrix`, `v_rule_impact` |
| Integration met extraction pipeline | 2 | Auto-link suggesties na rule extraction |
| Impact analysis queries | 1 | Welke stories/epics geraakt bij rule wijziging |

**Hiërarchie Model:**
```
EPIC (EP-001) "Agenda Management"
├── FEATURE (FT-001) "Afspraak Plannen"
│   ├── USER STORY (US-001) "Als hulpverlener wil ik..."
│   │   ├── BR-001 authorization
│   │   ├── BR-015 scheduling
│   │   └── BR-042 data_access
│   └── USER STORY (US-002) "Foutmelding bij overlap"
│       └── BR-042 data_access (hergebruik)
```

**Traceability API Endpoints:**
```
GET  /api/epics/{project_id}
GET  /api/epics/{epic_id}/features
GET  /api/features/{feature_id}/stories
GET  /api/stories/{story_id}/rules
GET  /api/rules/{rule_id}/impact
GET  /api/traceability/{project_id}/matrix
POST /api/traceability/link
```

**Use Cases:**
- Impact analyse: "Welke stories geraakt als BR-042 wijzigt?"
- Compliance: "Bewijs dat alle authorization rules getest zijn"
- Migration: "Welke rules moeten mee naar nieuw systeem?"

**Deliverables:**
- [ ] `alembic/versions/xxx_add_traceability_tables.py`
- [ ] `app/api/traceability.py` - API endpoints
- [ ] `app/services/traceability_service.py` - Business logic
- [ ] `tests/api/test_traceability_api.py`

### Week 113-114: Phase 5 - Agent & Workflow Integration (16 uur) ⭐ NEW

**Doel:** Integratie met bestaande MarQed workflows en agents

| Task | Uren | Output | Touches |
|------|------|--------|---------|
| BROWN_PAPER workflow hook | 4 | `workflows/brown_paper.py` | Miguel agent |
| MIGRATION workflow hook | 4 | `workflows/migration.py` | Miguel agent |
| BACKLOG_GENERATION integration | 4 | `services/backlog_service.py` | Peter agent |
| Agent prompt updates + tests | 4 | Agent context enrichment | Felix, Miguel, Peter |

**Workflow Integration Points:**

| Workflow | Integration Point | Agent | What They Receive |
|----------|-------------------|-------|-------------------|
| **BROWN_PAPER** | Step 2: Code Analysis | Miguel | 500+ rules, CRUD workflows, migration impact |
| **MIGRATION** | Step 3: Impact Analysis | Miguel | Rules requiring rewrite vs portable |
| **BACKLOG_GENERATION** | Step 1: Code Scan | Peter | Rules → User Stories mapping |
| **PROJECT_DEFINITION** | Step 4: Architecture | Felix | Rules als architectural constraints |

**Deliverables:**
- [ ] `app/workflows/brown_paper.py` - Business rule extraction hook
- [ ] `app/workflows/migration.py` - Impact analysis integration
- [ ] `app/services/backlog_service.py` - Rules → Stories mapping
- [ ] Agent prompt templates updated with rule context
- [ ] `tests/workflows/test_rule_integration.py`

### Total Effort Summary

| Phase | Uren | Focus |
|-------|------|-------|
| Phase 1: Hybrid Core Architecture | 24 | Base + VB.NET + ASP + Factory |
| Phase 2: Stored Procedures | 16 | T-SQL + PL/SQL |
| Phase 2.5: LLM-Assisted ⭐ | 20 | Classifier + Validator + Orchestrator |
| Phase 3: Business Rule Correlation | 24 | Workflow detection + Mermaid |
| Phase 4: Integration | 16 | API + DB + Dashboard |
| Phase 4.5: Traceability ⭐ | 12 | Epic/Feature/Story/Rule linkage |
| Phase 5: Workflow Integration ⭐ | 16 | BROWN_PAPER, MIGRATION, BACKLOG_GEN |
| **TOTAAL** | **128 uur** | **~4 weken full-time** |

---

## Gedachte-Items (Beyond Week 115)

| Repository | Concept | Priority | When |
|------------|---------|----------|------|
| **GitLab Integration** | Same as GitHub for GitLab repos | HIGH | Fase 13 |
| **Bitbucket Integration** | Same as GitHub for Bitbucket repos | MEDIUM | Fase 13 |
| **InsForge** | Natural language → backend infrastructure | LOW | Fase 14+ |
| **PraisonAI** | 100+ LLM support, deep research agents | LOW | Fase 14+ |
| **Agent-S** | GUI/Computer automation (69.9% accuracy) | LOW | Fase 14+ |
| **ToolForge** | Custom tool generation | MEDIUM | Fase 13 |
| **AgentFlow** | Visual workflow designer | MEDIUM | Fase 13 |

---

## Suggesties (Identified Improvements)

### BROWN_PAPER_ENHANCEMENT: Deep Analysis Integration

**Probleem:** BrownPaperService heeft eigen simpele regex-based analyse terwijl rijke analyse services bestaan.

**Huidige situatie (Week 125):**
```
BrownPaperService IMPORTS:
├── application_registry_service  ✅ (metadata)
├── brown_paper_estimation_service ✅ (FP/SP)
└── EIGEN regex analyse           ⚠️ (duplicatie)

BESCHIKBAAR MAAR NIET GEBRUIKT:
├── CodeAnalysisAggregatorService ❌ (complexity, coupling, cohesion)
├── DeepExtractionService         ❌ (multi-LLM council, INVEST)
├── HierarchicalStoryExtractionService ❌ (multi-level, CiRA)
├── LayeredAnalysisService        ❌ (VBScript, SWOT, stored procs)
└── DependencyGraphService        ❌ (graph structure, circular deps)
```

**Voorstel:**
1. Integreer `DependencyGraphService` in BrownPaperService voor:
   - Automatische module clustering
   - Circular dependency detectie
   - Coupling/cohesion metrics
   - Graph-based visualisatie data

2. Integreer `LayeredAnalysisService` voor VB.NET/ASP projecten:
   - VBScript analyse
   - Stored procedure detectie
   - SWOT generation

3. Optional: `DeepExtractionService` voor tier-aware analysis

**Impact:**
| Metric | Huidig | Na Integratie |
|--------|--------|---------------|
| Module relaties | Flat list | Graph met edges |
| Circular deps | Niet gedetecteerd | Automatisch gevonden |
| Complexity metrics | Geen | Cyclomatic, coupling |
| VBScript analyse | Regex | Dedicated analyzer |

**Effort:** 16-24 uur
**Priority:** MEDIUM
**Target:** Fase 14+
**Origin:** Week 125 Afspraak module analyse

---

## Technical Debt (Carry-Over)

| Priority | Task | Impact | Effort | Target |
|----------|------|--------|--------|--------|
| Medium | **Pydantic V2 Migration** | 92 deprecation warnings | 8-16 uur | Week 91+ |
| Low | FastAPI Lifespan Handlers | 3 warnings | 2 uur | Week 91+ |
| Low | Python 3.13 crypt Module | 1 warning | 1 uur | Before Python 3.13 |
| Low | datetime.utcnow() deprecation | 6 warnings | 2 uur | Week 91+ |

---

## Success Metrics (Week 90 Target)

| Metric | Current | Week 87 | Week 90 | Status |
|--------|---------|---------|---------|--------|
| Workflows fully integrated | 3/11 | 11/11 | 11/11 | 📋 PLANNED |
| Tools per workflow (avg) | 2.1 | 3.5 | 4.2 | 📋 PLANNED |
| Test coverage | 637+ | 700+ | 750+ | 📋 PLANNED |
| API endpoints | 420+ | 440+ | 460+ | 📋 PLANNED |
| **Extraction confidence** | 60% | **95%** | 95% | 📋 Week 81-87 |
| **FP coverage (Story/Task)** | 0% | **100%** | 100% | 📋 Week 81-87 |
| **Human review reduction** | baseline | **-87.5%** | -87.5% | 📋 Week 81-87 |

---

## Related Documentation

| Document | Content |
|----------|---------|
| [deep-extraction-pipeline.md](../architecture/deep-extraction-pipeline.md) | Full specification |
| [ROADMAP.md](../../ROADMAP.md) | High-level overview |
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | Technical architecture |
| [roadmap_done.md](roadmap_done.md) | Completed weeks (46-79) |
