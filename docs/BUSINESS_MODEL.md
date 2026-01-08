# Business Model: Deep Extraction Pipeline

**Version:** 1.0
**Date:** 2025-12-17
**Status:** PLANNED (Week 81-87)

---

## Executive Summary

Customer-selectable tier-based pricing voor AI-gedreven code extractie met:
- **5 Quality Tiers**: FREE ($0) tot PREMIUM ($150+ base)
- **LOC Scaling**: 0-2M+ lines of code
- **Complexity Multiplier**: 1.0× tot 5.0× based on stack assessment
- **Re-Run Capability**: Upgrade tier, betaal verschil, krijg betere resultaten

**Target Margins:** 75-96% op betaalde tiers

---

## Table of Contents

1. [Pricing Components](#1-pricing-components)
2. [Quality Tiers](#2-quality-tiers)
3. [LOC Scaling](#3-loc-scaling)
4. [Complexity Assessment](#4-complexity-assessment)
5. [Pricing Calculator](#5-pricing-calculator)
6. [Example Scenarios](#6-example-scenarios)
7. [Cost Structure](#7-cost-structure)
8. [GitHub/DevOps Analysis](#8-githubdevops-analysis)
9. [Revenue Projections](#9-revenue-projections)
10. [Competitive Analysis](#10-competitive-analysis)

---

## 1. Pricing Components

### Formula

```
Final Price = Base Tier Price × LOC Multiplier × Complexity Multiplier
```

| Component | Range | Description |
|-----------|-------|-------------|
| **Base Tier** | $0 - $150 | Customer kiest quality level |
| **LOC Multiplier** | 0.5× - 25× | Schaal based on codebase size |
| **Complexity Multiplier** | 1.0× - 5.0× | Stack complexity assessment |

### Minimum Price Rule

```python
final_price = max(base_price, calculated_price)
```

FREE tier blijft altijd $0, ongeacht LOC of complexity.

---

## 2. Quality Tiers

### Tier Overview

| Tier | Base Price | Target Confidence | LLMs Used | Human Review | Best For |
|------|------------|-------------------|-----------|--------------|----------|
| **FREE** | $0 | 60% | 3 (Ollama) | No | Evaluatie, kleine projecten |
| **BASIC** | $5 | 70% | 5 | No | Simpele codebases |
| **STANDARD** | $25 | 80% | 7 | No | Meeste projecten |
| **PROFESSIONAL** | $75 | 90% | 9 | Optional | Enterprise projecten |
| **PREMIUM** | $150 | 95% | 10+ | Included | Mission-critical, legacy |

### Tier Details

#### FREE ($0)
- 3 Ollama LLMs parallel (Qwen-Coder, DeepSeek-R1, CodeLlama)
- Cycle 1 + Cycle 5 only (skip cross-validation)
- Basic Epic/Feature extraction
- No Function Point estimates
- No human review
- **Use case:** Evaluatie, proof of concept, hobby projecten

#### BASIC ($5 base)
- FREE + Groq (Llama 3.1) + Alibaba (Qwen-Turbo)
- Still Cycle 1 + 5 (fast extraction)
- Improved cross-validation
- Basic FP estimates
- **Use case:** Kleine moderne codebases, startups

#### STANDARD ($25 base) - RECOMMENDED
- BASIC + Gemini Flash-Lite + Gemini 2.5 Flash
- Adds Cycle 2 (Cross-Enrichment via Gemini Flash)
- Full Epic → Feature → Story → Task hierarchy
- IFPUG-based Function Point estimates
- **Use case:** Meeste enterprise projecten

#### PROFESSIONAL ($75 base)
- STANDARD + GPT-5.2 + Moonshot Kimi
- Adds Cycle 3 (Dual-model conflict detection: Gemini Pro + GPT-5.2)
- Optional human review for edge cases
- Risk assessment per Epic
- **Use case:** Grote enterprise projecten, migraties

#### PREMIUM ($150 base)
- PROFESSIONAL + Claude Haiku in Cycle 1
- Full 5-cycle pipeline including Cycle 4 (Human Review)
- Claude Opus 4.5 final synthesis
- Confidence explanations per extraction
- Dedicated support
- **Use case:** Mission-critical systems, complex legacy, compliance-required

---

## 3. LOC Scaling

### LOC Multiplier Table

| LOC Range | Multiplier | Rationale |
|-----------|------------|-----------|
| 0 - 10K | 0.5× | Micro projects, quick scan |
| 10K - 25K | 0.7× | Small projects |
| 25K - 50K | 1.0× | **Baseline** |
| 50K - 100K | 1.8× | Medium projects |
| 100K - 250K | 3.0× | Large projects |
| 250K - 500K | 5.0× | Enterprise systems |
| 500K - 1M | 8.0× | Large enterprise |
| 1M - 2M | 12.0× | Mega projects |
| 2M+ | 25.0× + custom | Enterprise custom quote |

### LOC Scaling Rationale

```
Tokens required ≈ LOC × 2-5 (depending on language verbosity)
Processing time ≈ LOC × complexity
LLM calls ≈ ceil(LOC / chunk_size) × num_llms × cycles
```

**Niet-lineaire scaling** omdat:
- Grotere codebases hebben meer cross-references
- Context windows moeten vaker ge-chunked worden
- Conflict resolution neemt toe met size
- Human review tijd schaalt mee

---

## 4. Complexity Assessment

### Complexity Score (0-100)

| Score Range | Category | Multiplier |
|-------------|----------|------------|
| 0-20 | Simple | 1.0× |
| 21-40 | Medium | 1.5× |
| 41-60 | Complex | 2.0× |
| 61-80 | Very Complex | 3.0× |
| 81-100 | Extreme/Legacy | 5.0× |

### Complexity Factors

#### A. Language Diversity (0-25 points)

| Languages | Points | Examples |
|-----------|--------|----------|
| 1 | 0 | Pure C# solution |
| 2-3 | 8 | C# + TypeScript + SQL |
| 4-5 | 15 | C#, VB.NET, JS, T-SQL, PowerShell |
| 6-8 | 20 | Multi-stack enterprise |
| 9+ | 25 | Polyglot nightmare |

#### B. Framework Age & Type (0-25 points)

| Framework Age | Points | Examples |
|---------------|--------|----------|
| < 3 years | 0 | .NET 8, React 18, Vue 3 |
| 3-7 years | 8 | .NET Core 3.1, Angular 8 |
| 7-12 years | 15 | MVC 5, AngularJS, jQuery |
| 12-20 years | 20 | WebForms, WCF, Silverlight |
| 20+ years | 25 | VB6, Classic ASP, COM+ |

#### C. Database Complexity (0-20 points)

| Type | Points | Examples |
|------|--------|----------|
| Modern ORM only | 0 | EF Core, Prisma |
| ORM + raw SQL | 5 | EF + Dapper |
| Stored Procedures (< 100) | 10 | Legacy with some SP |
| Heavy SP (100-500) | 15 | SP-centric architecture |
| Extreme SP (500+) + Triggers | 20 | Mainframe-style DB |

#### D. Platform Diversity (0-15 points)

| Platforms | Points | Examples |
|-----------|--------|----------|
| Single platform | 0 | Web only |
| Web + API | 3 | Standard SaaS |
| Web + Mobile (1 OS) | 6 | iOS OR Android |
| Web + Mobile (both) | 10 | iOS + Android |
| Web + Mobile + Desktop + Cloud | 15 | Full omnichannel |

#### E. Integration Complexity (0-10 points)

| Type | Points | Examples |
|------|--------|----------|
| REST APIs only | 0 | Modern microservices |
| REST + SOAP | 3 | Mixed integration |
| COM/DCOM/ActiveX | 6 | Windows legacy |
| Mainframe/AS400/Custom | 10 | Enterprise legacy |

#### F. Repository Structure (0-5 points)

| Structure | Points | Examples |
|-----------|--------|----------|
| Monorepo (clean) | 0 | Nx, Turborepo |
| Multi-repo (< 5) | 2 | Microservices |
| Multi-repo (5-20) | 3 | Large enterprise |
| Multi-repo (20+) | 5 | Mega enterprise |

### Complexity Score Calculator

```python
def calculate_complexity_score(analysis: ProjectAnalysis) -> tuple[int, float]:
    """
    Calculate complexity score (0-100) and multiplier (1.0-5.0).
    """
    score = 0

    # A. Language Diversity (0-25)
    lang_count = len(analysis.languages)
    if lang_count >= 9:
        score += 25
    elif lang_count >= 6:
        score += 20
    elif lang_count >= 4:
        score += 15
    elif lang_count >= 2:
        score += 8

    # B. Framework Age (0-25)
    oldest_years = analysis.oldest_framework_age_years
    if oldest_years >= 20:
        score += 25
    elif oldest_years >= 12:
        score += 20
    elif oldest_years >= 7:
        score += 15
    elif oldest_years >= 3:
        score += 8

    # C. Database Complexity (0-20)
    sp_count = analysis.stored_procedure_count
    has_triggers = analysis.has_complex_triggers
    if sp_count >= 500 or has_triggers:
        score += 20
    elif sp_count >= 100:
        score += 15
    elif sp_count >= 1:
        score += 10
    elif analysis.has_raw_sql:
        score += 5

    # D. Platform Diversity (0-15)
    platforms = analysis.target_platforms  # ['web', 'ios', 'android', 'desktop', 'cloud']
    if len(platforms) >= 4:
        score += 15
    elif 'ios' in platforms and 'android' in platforms:
        score += 10
    elif len(platforms) >= 2:
        score += 6
    elif len(platforms) == 2:
        score += 3

    # E. Integration Complexity (0-10)
    if analysis.has_mainframe_integration:
        score += 10
    elif analysis.has_com_integration:
        score += 6
    elif analysis.has_soap_services:
        score += 3

    # F. Repository Structure (0-5)
    repo_count = analysis.repository_count
    if repo_count >= 20:
        score += 5
    elif repo_count >= 5:
        score += 3
    elif repo_count >= 2:
        score += 2

    # Convert to multiplier
    if score >= 81:
        multiplier = 5.0  # Extreme
    elif score >= 61:
        multiplier = 3.0  # Very Complex
    elif score >= 41:
        multiplier = 2.0  # Complex
    elif score >= 21:
        multiplier = 1.5  # Medium
    else:
        multiplier = 1.0  # Simple

    return score, multiplier
```

---

## 5. Pricing Calculator

### Complete Pricing Algorithm

```python
from dataclasses import dataclass
from typing import Literal

TierName = Literal["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]

TIER_BASE_PRICES = {
    "FREE": 0,
    "BASIC": 5,
    "STANDARD": 25,
    "PROFESSIONAL": 75,
    "PREMIUM": 150
}

LOC_MULTIPLIERS = [
    (0, 10_000, 0.5),
    (10_000, 25_000, 0.7),
    (25_000, 50_000, 1.0),
    (50_000, 100_000, 1.8),
    (100_000, 250_000, 3.0),
    (250_000, 500_000, 5.0),
    (500_000, 1_000_000, 8.0),
    (1_000_000, 2_000_000, 12.0),
    (2_000_000, float('inf'), 25.0),
]

@dataclass
class PricingResult:
    tier: TierName
    base_price: float
    loc: int
    loc_multiplier: float
    complexity_score: int
    complexity_multiplier: float
    final_price: float
    our_estimated_cost: float
    margin_percentage: float


def get_loc_multiplier(loc: int) -> float:
    for min_loc, max_loc, mult in LOC_MULTIPLIERS:
        if min_loc <= loc < max_loc:
            return mult
    return 25.0  # 2M+


def calculate_our_cost(loc: int, complexity_mult: float, tier: str) -> float:
    """
    Estimate our LLM costs based on LOC and tier.
    Ollama is free, external LLMs scale with tokens.
    """
    # Base token estimate: ~3 tokens per LOC average
    estimated_tokens = loc * 3

    # Cost per million tokens (weighted average based on tier)
    tier_cost_per_m = {
        "FREE": 0,  # All Ollama
        "BASIC": 0.10,  # Mostly Ollama + cheap externals
        "STANDARD": 0.50,  # Adds Gemini Flash
        "PROFESSIONAL": 2.00,  # Adds Gemini Pro + GPT-5.2
        "PREMIUM": 5.00,  # Adds Claude Opus
    }

    base_cost = (estimated_tokens / 1_000_000) * tier_cost_per_m[tier]

    # Complexity adds ~20% cost per multiplier point above 1.0
    complexity_overhead = 1 + (complexity_mult - 1) * 0.2

    return base_cost * complexity_overhead


def calculate_price(
    tier: TierName,
    loc: int,
    complexity_score: int,
    complexity_multiplier: float
) -> PricingResult:
    """Calculate final extraction price."""
    base = TIER_BASE_PRICES[tier]

    if base == 0:  # FREE tier
        return PricingResult(
            tier=tier,
            base_price=0,
            loc=loc,
            loc_multiplier=get_loc_multiplier(loc),
            complexity_score=complexity_score,
            complexity_multiplier=complexity_multiplier,
            final_price=0,
            our_estimated_cost=0,
            margin_percentage=0
        )

    loc_mult = get_loc_multiplier(loc)
    calculated = base * loc_mult * complexity_multiplier
    final = max(base, round(calculated))

    our_cost = calculate_our_cost(loc, complexity_multiplier, tier)
    margin = ((final - our_cost) / final * 100) if final > 0 else 0

    return PricingResult(
        tier=tier,
        base_price=base,
        loc=loc,
        loc_multiplier=loc_mult,
        complexity_score=complexity_score,
        complexity_multiplier=complexity_multiplier,
        final_price=final,
        our_estimated_cost=round(our_cost, 2),
        margin_percentage=round(margin, 1)
    )
```

---

## 6. Example Scenarios

### Scenario 1: Modern Startup SaaS
**Stack:** Next.js 14, TypeScript, Prisma, PostgreSQL
**LOC:** 35K
**Complexity Score:** 12 (Simple, 1.0×)

| Tier | Base | LOC (1.0×) | Complexity (1.0×) | **Final** | Our Cost | Margin |
|------|------|------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $5 | $5 | **$5** | $0.10 | 98% |
| STANDARD | $25 | $25 | $25 | **$25** | $0.50 | 98% |
| PROFESSIONAL | $75 | $75 | $75 | **$75** | $2.00 | 97% |
| PREMIUM | $150 | $150 | $150 | **$150** | $5.00 | 97% |

---

### Scenario 2: Corporate .NET Application
**Stack:** .NET 6, Vue 2 (outdated), SQL Server with 80 SPs
**LOC:** 95K
**Complexity Score:** 38 (Medium, 1.5×)

| Tier | Base | LOC (1.8×) | Complexity (1.5×) | **Final** | Our Cost | Margin |
|------|------|------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $9 | $13.50 | **$14** | $0.40 | 97% |
| STANDARD | $25 | $45 | $67.50 | **$68** | $2.00 | 97% |
| PROFESSIONAL | $75 | $135 | $202.50 | **$203** | $8.00 | 96% |
| PREMIUM | $150 | $270 | $405 | **$405** | $20.00 | 95% |

---

### Scenario 3: Enterprise Multi-Platform
**Stack:** .NET MVC 5, Xamarin (iOS + Android), Angular 8, SQL Server + 250 SPs
**LOC:** 320K
**Complexity Score:** 58 (Complex, 2.0×)

| Tier | Base | LOC (5.0×) | Complexity (2.0×) | **Final** | Our Cost | Margin |
|------|------|------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $25 | $50 | **$50** | $1.50 | 97% |
| STANDARD | $25 | $125 | $250 | **$250** | $8.00 | 97% |
| PROFESSIONAL | $75 | $375 | $750 | **$750** | $30.00 | 96% |
| PREMIUM | $150 | $750 | $1,500 | **$1,500** | $80.00 | 95% |

---

### Scenario 4: Legacy Healthcare System (HCI-CRS style)
**Stack:** VB.NET, C#, Classic ASP, VBScript, COM+, WebForms, 500+ SPs
**LOC:** 450K
**Complexity Score:** 78 (Very Complex, 3.0×)

| Tier | Base | LOC (5.0×) | Complexity (3.0×) | **Final** | Our Cost | Margin |
|------|------|------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $25 | $75 | **$75** | $3.00 | 96% |
| STANDARD | $25 | $125 | $375 | **$375** | $15.00 | 96% |
| PROFESSIONAL | $75 | $375 | $1,125 | **$1,125** | $60.00 | 95% |
| PREMIUM | $150 | $750 | $2,250 | **$2,250** | $150.00 | 93% |

---

### Scenario 5: Mega Enterprise Omnichannel
**Stack:** 12 languages, Web + iOS + Android + Desktop + Cloud, 40 repos, Mainframe integration, 800+ SPs
**LOC:** 1.8M
**Complexity Score:** 95 (Extreme, 5.0×)

| Tier | Base | LOC (12.0×) | Complexity (5.0×) | **Final** | Our Cost | Margin |
|------|------|-------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $60 | $300 | **$300** | $15.00 | 95% |
| STANDARD | $25 | $300 | $1,500 | **$1,500** | $75.00 | 95% |
| PROFESSIONAL | $75 | $900 | $4,500 | **$4,500** | $300.00 | 93% |
| PREMIUM | $150 | $1,800 | $9,000 | **$9,000** | $800.00 | 91% |

---

### Scenario 6: Massive Legacy Transformation
**Stack:** COBOL interface, VB6, .NET 2.0, Oracle + 1200 SPs, AS400 integration
**LOC:** 2.5M
**Complexity Score:** 100 (Extreme, 5.0×)

| Tier | Base | LOC (25.0×) | Complexity (5.0×) | **Final** | Our Cost | Margin |
|------|------|-------------|-------------------|-----------|----------|--------|
| FREE | $0 | - | - | **$0** | $0 | - |
| BASIC | $5 | $125 | $625 | **$625** | $35.00 | 94% |
| STANDARD | $25 | $625 | $3,125 | **$3,125** | $180.00 | 94% |
| PROFESSIONAL | $75 | $1,875 | $9,375 | **$9,375** | $700.00 | 93% |
| PREMIUM | $150 | $3,750 | $18,750 | **$18,750** | $2,000.00 | 89% |

---

## 7. Cost Structure

### Our LLM Costs per Provider

| Provider | Model | Input/1M | Output/1M | Use Case |
|----------|-------|----------|-----------|----------|
| **Ollama** | Qwen-Coder, DeepSeek, CodeLlama | $0 | $0 | Bulk analysis |
| **Groq** | Llama 3.1 8B | $0.05 | $0.08 | Fast validation |
| **Alibaba** | Qwen-Turbo | $0.05 | $0.20 | Cross-check |
| **Google** | Gemini 2.0 Flash-Lite | $0.075 | $0.30 | Cheap external |
| **Google** | Gemini 2.5 Flash | $0.30 | $2.50 | Cross-enrichment |
| **Google** | Gemini 2.5 Pro | $1.25 | $10.00 | Conflict detection |
| **Google** | Gemini 3 Pro | $2.00 | $12.00 | Pro synthesis |
| **OpenAI** | GPT-5.2 | $1.75 | $14.00 | Dual validation |
| **Moonshot** | Kimi K2 | $0.55 | $2.18 | Additional perspective |
| **Anthropic** | Claude Haiku | $0.80 | $4.00 | Fast Claude |
| **Anthropic** | Claude Opus 4.5 | $5.00 | $25.00 | Premium synthesis |

### Cost Scaling by Tier

| Tier | Avg Cost per 50K LOC | Cost Drivers |
|------|----------------------|--------------|
| FREE | $0 | 100% Ollama |
| BASIC | ~$0.50 | Ollama + Groq + Qwen |
| STANDARD | ~$5.00 | + Gemini Flash |
| PROFESSIONAL | ~$15.00 | + Gemini Pro + GPT-5.2 |
| PREMIUM | ~$25.00 | + Claude Opus |

### Margin Analysis

| Scenario | Price Range | Cost Range | Margin Range |
|----------|-------------|------------|--------------|
| Simple small (< 50K) | $5 - $150 | $0.10 - $5 | 97-98% |
| Medium (50K-250K) | $14 - $750 | $0.50 - $30 | 95-97% |
| Complex (250K-1M) | $50 - $4,500 | $3 - $300 | 93-96% |
| Extreme (1M+) | $300 - $18,750 | $35 - $2,000 | 89-95% |

---

## 8. GitHub/DevOps Analysis

### Feature Overview (Planned: Week 88+)

Naast code-analyse ook repository metadata analyseren voor betere extraction:

| Data Source | Insights | Impact on Extraction |
|-------------|----------|---------------------|
| **Commit History** | Active areas, change frequency | Focus extraction on hot spots |
| **Branch Strategy** | Feature branches, release cycles | Identify release scope |
| **PR History** | Review patterns, merge conflicts | Identify complex areas |
| **Issues/Bugs** | Known problems, feature requests | Pre-populate backlog items |
| **CI/CD Pipelines** | Build complexity, test coverage | Quality indicators |
| **Contributors** | Team structure, knowledge silos | Risk assessment |
| **Dependencies** | Package versions, vulnerabilities | Tech debt scoring |

### GitHub Analysis Endpoints (Planned)

```
POST /api/github/analyze
{
    "repo_url": "https://github.com/org/repo",
    "access_token": "ghp_...",
    "analysis_depth": "full|quick",
    "include_history": true
}

Response:
{
    "repository_metrics": {
        "total_commits": 5234,
        "active_contributors": 12,
        "branches": 45,
        "open_prs": 8,
        "open_issues": 156
    },
    "complexity_indicators": {
        "change_frequency_score": 72,
        "merge_conflict_rate": 0.15,
        "avg_pr_review_time_hours": 24,
        "test_coverage_trend": "declining"
    },
    "hot_spots": [
        {"path": "src/legacy/auth", "change_count": 234, "bug_count": 12},
        {"path": "src/api/payments", "change_count": 189, "bug_count": 8}
    ],
    "suggested_epics_from_issues": [
        {"title": "Authentication Refactor", "related_issues": [45, 67, 89]},
        {"title": "Payment Gateway Update", "related_issues": [23, 56]}
    ]
}
```

### Azure DevOps Analysis (Planned)

```
POST /api/devops/analyze
{
    "organization": "myorg",
    "project": "myproject",
    "pat_token": "...",
    "include_pipelines": true,
    "include_boards": true
}

Response:
{
    "repository_metrics": {...},
    "pipeline_analysis": {
        "build_success_rate": 0.87,
        "avg_build_time_minutes": 12,
        "deployment_frequency": "daily"
    },
    "board_analysis": {
        "backlog_items": 234,
        "active_sprints": 2,
        "velocity_trend": "stable"
    },
    "work_items_for_extraction": [
        {"id": 1234, "title": "Migrate to .NET 8", "type": "Epic"},
        {"id": 1235, "title": "Security audit", "type": "Feature"}
    ]
}
```

### Integration with Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│  ENHANCED EXTRACTION FLOW                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. GitHub/DevOps Analysis (Optional, +$10-50)                     │
│     ├── Repository metrics                                         │
│     ├── Hot spot identification                                    │
│     ├── Issue/Bug correlation                                      │
│     └── Team structure analysis                                    │
│                                                                     │
│  2. Code Analysis (Standard extraction)                            │
│     ├── Cycle 1: Independent LLM analysis                         │
│     ├── Cycle 2: Cross-enrichment                                 │
│     ├── Cycle 3: Conflict detection                               │
│     └── Cycle 5: Final synthesis                                  │
│                                                                     │
│  3. Combined Output                                                │
│     ├── Code-derived Epics/Features/Stories                       │
│     ├── GitHub-derived backlog suggestions                        │
│     ├── Hot spot prioritization                                   │
│     └── Team/risk analysis                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Pricing Add-on

| Analysis Type | Base Price | Per 1000 Commits | Per 100 PRs |
|---------------|------------|------------------|-------------|
| GitHub Quick | $10 | +$2 | +$1 |
| GitHub Full | $25 | +$5 | +$2 |
| Azure DevOps Quick | $15 | +$2 | +$1 |
| Azure DevOps Full | $35 | +$5 | +$2 |

---

## 9. Revenue Projections

### Conservative Scenario (Year 1)

| Quarter | Projects | Avg Price | Revenue | Costs | Net |
|---------|----------|-----------|---------|-------|-----|
| Q1 | 50 | $75 | $3,750 | $400 | $3,350 |
| Q2 | 100 | $100 | $10,000 | $1,000 | $9,000 |
| Q3 | 150 | $150 | $22,500 | $2,500 | $20,000 |
| Q4 | 200 | $200 | $40,000 | $4,500 | $35,500 |
| **Year 1** | **500** | **$153** | **$76,250** | **$8,400** | **$67,850** |

### Moderate Scenario (Year 1)

| Quarter | Projects | Avg Price | Revenue | Costs | Net |
|---------|----------|-----------|---------|-------|-----|
| Q1 | 100 | $150 | $15,000 | $1,500 | $13,500 |
| Q2 | 200 | $200 | $40,000 | $4,000 | $36,000 |
| Q3 | 350 | $250 | $87,500 | $9,000 | $78,500 |
| Q4 | 500 | $300 | $150,000 | $16,000 | $134,000 |
| **Year 1** | **1,150** | **$254** | **$292,500** | **$30,500** | **$262,000** |

### Enterprise Scenario (Year 1)

Includes large legacy transformation projects:

| Quarter | Projects | Avg Price | Revenue | Costs | Net |
|---------|----------|-----------|---------|-------|-----|
| Q1 | 20 | $2,000 | $40,000 | $5,000 | $35,000 |
| Q2 | 35 | $2,500 | $87,500 | $10,000 | $77,500 |
| Q3 | 50 | $3,000 | $150,000 | $18,000 | $132,000 |
| Q4 | 75 | $3,500 | $262,500 | $30,000 | $232,500 |
| **Year 1** | **180** | **$3,000** | **$540,000** | **$63,000** | **$477,000** |

---

## 10. Competitive Analysis

### Market Positioning

| Competitor | Target | Price/50K LOC | Confidence | Our Advantage |
|------------|--------|---------------|------------|---------------|
| **Manual extraction** | Enterprise | $2,000-5,000 | 95%+ (slow) | 97% cheaper, faster |
| **Single-LLM tools** | SMB | $50-100 | 50-60% | Better accuracy |
| **Enterprise tools** | Enterprise | $500+ | 70-80% | Better value |
| **Consulting firms** | Enterprise | $10,000+ | 90%+ | 95% cheaper |
| **Us (STANDARD)** | All | $25-250 | 80% | Best value |
| **Us (PREMIUM)** | Enterprise | $150-18,750 | 95% | Best accuracy + value |

### Key Differentiators

1. **Tier Flexibility**: Start FREE, upgrade when needed
2. **Re-Run Capability**: Improve results, pay difference only
3. **Multi-LLM Consensus**: Better than single-model approaches
4. **Transparent Pricing**: Clear formula, no surprises
5. **Human-in-Loop Option**: For mission-critical accuracy
6. **GitHub/DevOps Integration**: Repository context enhances extraction

---

## Appendix: Quick Reference

### Price Quick Calculator

```
Simple project (score < 20):
  Price = Base × LOC_mult × 1.0

Medium project (score 21-40):
  Price = Base × LOC_mult × 1.5

Complex project (score 41-60):
  Price = Base × LOC_mult × 2.0

Very complex (score 61-80):
  Price = Base × LOC_mult × 3.0

Extreme/Legacy (score 81+):
  Price = Base × LOC_mult × 5.0
```

### LOC Quick Reference

| LOC | Multiplier |
|-----|------------|
| 25K | 0.7× |
| 50K | 1.0× |
| 100K | 1.8× |
| 250K | 3.0× |
| 500K | 5.0× |
| 1M | 8.0× |
| 2M | 12.0× |
| 2M+ | 25.0× |

### Example Quick Calculations

```
100K LOC, Simple, STANDARD:
  $25 × 1.8 × 1.0 = $45

500K LOC, Complex, PROFESSIONAL:
  $75 × 5.0 × 2.0 = $750

1.5M LOC, Extreme, PREMIUM:
  $150 × 12.0 × 5.0 = $9,000
```

---

## Related Documentation

| Document | Content |
|----------|---------|
| [deep-extraction-pipeline.md](architecture/deep-extraction-pipeline.md) | Technical specification |
| [ROADMAP.md](../ROADMAP.md) | Implementation timeline |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | System architecture |

---

**Document History:**
- v1.0 (2025-12-17): Initial business model with LOC/complexity pricing
