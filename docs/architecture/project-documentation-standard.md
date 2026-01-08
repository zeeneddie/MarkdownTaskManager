# Project Documentation Standard

**Status**: DRAFT
**Doel**: Gestandaardiseerde documentatie structuur voor alle projecten in het platform
**Last Updated**: 2025-11-26

---

## 1. Huidige Situatie

### Bestaande Structuur (Projecten/klaverjas-competitie/)
```
Projecten/{project-name}/
├── kanban.md                    # Task board
├── EPIC-001-{name}/
│   ├── epic.md                  # Epic definitie
│   ├── README.md                # Epic overview
│   └── FEAT-001-{name}.md       # Feature specs
└── EPIC-002-{name}/
    └── ...
```

### Wat Ontbreekt
- **Onboarding documentatie**
- **Architectuur beslissingen (ADRs)**
- **Project metadata & configuratie**
- **Review history & council consensus**
- **Roadmap & planning documenten**

---

## 2. Voorgestelde Standaard Structuur

```
Projecten/{project-name}/
│
├── .project/                        # Project metadata (hidden)
│   ├── config.json                  # Project configuratie
│   ├── council-history.json         # LLM Council review history
│   └── quality-scores.json          # Quality gate scores over tijd
│
├── docs/                            # Alle project documentatie
│   ├── ONBOARDING.md                # Developer onboarding (council-verified)
│   ├── ARCHITECTURE.md              # System architecture
│   ├── ROADMAP.md                   # Project roadmap
│   ├── TECH-STACK.md                # Technology decisions
│   │
│   ├── decisions/                   # Architecture Decision Records
│   │   ├── ADR-001-database-choice.md
│   │   ├── ADR-002-auth-strategy.md
│   │   └── ...
│   │
│   └── reviews/                     # LLM Council reviews
│       ├── onboarding/
│       │   ├── COUNCIL_CONSENSUS.md # Final consensus
│       │   ├── round-1-review.md    # Individual reviews
│       │   ├── round-2-review.md
│       │   ├── round-3-review.md
│       │   └── human-feedback.md    # Human corrections
│       └── architecture/
│           └── ...
│
├── epics/                           # Epic definitions (renamed from EPIC-XXX)
│   ├── data-export/
│   │   ├── epic.md
│   │   └── features/
│   │       ├── excel-export.md
│   │       ├── csv-export.md
│   │       └── pdf-export.md
│   └── mobile-app/
│       └── ...
│
├── kanban.md                        # Task board
├── archive.md                       # Completed tasks
└── README.md                        # Project overview (generated from ONBOARDING.md)
```

---

## 3. Human-in-the-Loop Council Workflow

### 3.1 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM COUNCIL + HUMAN REVIEW                           │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 1: INDIVIDUAL GENERATION                                     │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│  │  │   Ollama    │  │   Claude    │  │   Codex     │               │  │
│  │  │  (budget)   │  │ (quality)   │  │  (verify)   │               │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │  │
│  │         │                │                │                       │  │
│  │         └────────────────┼────────────────┘                       │  │
│  │                          ↓                                        │  │
│  │                   3 Draft Versions                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 2: ROUND-ROBIN PEER REVIEW                                   │  │
│  │                                                                    │  │
│  │  Ollama ──review──> Claude ──review──> Codex ──review──> Ollama   │  │
│  │                                                                    │  │
│  │  Output: 3 Review Reports + Scores                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 3: ORCHESTRATOR SYNTHESIS                                    │  │
│  │                                                                    │  │
│  │  • Identificeer consensus punten                                  │  │
│  │  • Combineer beste elementen                                      │  │
│  │  • Markeer onzekerheden/conflicten                                │  │
│  │                                                                    │  │
│  │  Output: Draft Consensus + Uncertainty List                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 4: HUMAN REVIEW (NEW!)                                       │  │
│  │                                                                    │  │
│  │  Human krijgt te zien:                                            │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ A. Draft Consensus Document                                 │  │  │
│  │  │ B. Per Provider: wat was correct? (checkboxes)              │  │  │
│  │  │ C. Uncertainty/Conflict lijst (resolve needed)              │  │  │
│  │  │ D. "Add missing information" text field                     │  │  │
│  │  │ E. "Nuances/corrections" text field                         │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │                                                                    │  │
│  │  Human actions:                                                   │  │
│  │  • Mark correct items per provider                                │  │
│  │  • Resolve conflicts                                              │  │
│  │  • Add missing context                                            │  │
│  │  • Make nuanced corrections                                       │  │
│  │  • Approve or request re-synthesis                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 5: FINAL SYNTHESIS                                           │  │
│  │                                                                    │  │
│  │  Orchestrator verwerkt human feedback:                            │  │
│  │  • Integreert correcties                                          │  │
│  │  • Voegt missing info toe                                         │  │
│  │  • Past nuances aan                                               │  │
│  │                                                                    │  │
│  │  Output: FINAL Consensus Document                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ FASE 6: STORAGE & VERSIONING                                      │  │
│  │                                                                    │  │
│  │  MD Files:                                                        │  │
│  │  • docs/ONBOARDING.md (final)                                     │  │
│  │  • docs/reviews/onboarding/*.md (all rounds)                      │  │
│  │                                                                    │  │
│  │  Database:                                                        │  │
│  │  • council_sessions (metadata)                                    │  │
│  │  • council_reviews (individual reviews)                           │  │
│  │  • council_consensus (consensus + human feedback)                 │  │
│  │  • document_versions (version history)                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Human Review Interface

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LLM Council Review - Onboarding Document                               │
│  Project: klaverjas-competitie                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DRAFT CONSENSUS                                              [Expand]  │
│  ─────────────────────────────────────────────────────────────────────  │
│  # Klaverjas Competitie Onboarding                                      │
│  Een beheer- en registratieplatform voor Klaverjascompetities...        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PROVIDER CONTRIBUTIONS - Wat was correct?                              │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  OLLAMA (qwen2.5-coder:7b) - Score: 35/100                             │
│  ├─ [✓] DDD architectuur beschrijving                                   │
│  ├─ [✓] Basis layer indeling                                            │
│  ├─ [ ] Next priorities (incorrect - features al af)                    │
│  └─ [ ] Setup commands (make quickstart bestaat niet)                   │
│                                                                         │
│  CLAUDE (Sonnet 4.5) - Score: 55/100                                   │
│  ├─ [✓] Pro Tips sectie                                                 │
│  ├─ [✓] Docker-first emphasis                                           │
│  ├─ [✓] "geen digitaal speelbord" afbakening                            │
│  ├─ [ ] make quickstart (incorrect)                                     │
│  └─ [ ] 385 tests (incorrect - 28 files)                                │
│                                                                         │
│  CODEX (gpt-5.1-max) - Score: 65/100                                   │
│  ├─ [✓] DDD dependency direction uitleg                                 │
│  ├─ [✓] Token-efficient output                                          │
│  ├─ [ ] Te beknopt voor complete onboarding                             │
│  └─ [ ] Mist praktische tips                                            │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CONFLICTS TO RESOLVE                                                   │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  1. Start Command                                                       │
│     ○ make quickstart (Ollama, Claude, Codex)                          │
│     ● ./dev.sh quickstart (Codex verified)        [SELECTED]           │
│     ○ Other: _______________                                            │
│                                                                         │
│  2. Test Count                                                          │
│     ○ 385 tests (Claude)                                                │
│     ● 28 test files (Codex verified)              [SELECTED]           │
│     ○ Other: _______________                                            │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MISSING INFORMATION                                                    │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Wat hebben alle drie de LLMs gemist dat je wilt toevoegen?             │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ - De database migraties worden automatisch uitgevoerd bij start   │ │
│  │ - Er is een seed script voor test data: ./dev.sh seed             │ │
│  │ - Hot-reload werkt alleen voor Python files, niet templates       │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  NUANCES & CORRECTIONS                                                  │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Wil je iets nuanceren of corrigeren in het consensus document?         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ - "Features 1-7 compleet" klopt, maar Feature 6 heeft nog een     │ │
│  │   known issue met NAT berekening bij gelijke stands               │ │
│  │ - De architecture is DDD maar met enkele compromissen in de       │ │
│  │   presentation layer voor snelheid                                │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Re-synthesize]  [Approve & Save]  [Save Draft]  [Cancel]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Opslag Strategie: Hybrid (MD + DB)

### 4.1 Waarom Hybrid?

| Aspect | MD Files | Database |
|--------|----------|----------|
| **Human readable** | Excellent | Poor |
| **Version control** | Git native | Requires migration |
| **Queryable** | Limited (grep) | Full SQL/API |
| **API access** | Requires parsing | Native |
| **Offline access** | Yes | Server required |
| **Collaboration** | Git workflow | Real-time |

**Conclusie**: Gebruik beide voor hun sterke punten.

### 4.2 Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  LLM Council    │     │    Database     │     │   MD Files      │
│  (Generation)   │────>│  (Structured)   │────>│  (Human Access) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ↓
                        ┌─────────────────┐
                        │   API Access    │
                        │  (Dashboards)   │
                        └─────────────────┘
```

### 4.3 Database Schema (Uitbreiding)

```sql
-- Council sessions (new)
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    document_type VARCHAR(50) NOT NULL,  -- 'onboarding', 'architecture', 'adr'
    status VARCHAR(20) DEFAULT 'draft',  -- draft, reviewing, human_review, approved
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(100)
);

-- Individual LLM reviews
CREATE TABLE council_reviews (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    round_number INTEGER NOT NULL,
    reviewer_model VARCHAR(100) NOT NULL,  -- 'claude/sonnet', 'codex/gpt-5.1-max'
    reviewed_model VARCHAR(100) NOT NULL,
    score INTEGER,
    review_content JSONB NOT NULL,  -- Full review as JSON
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consensus documents
CREATE TABLE council_consensus (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    version INTEGER DEFAULT 1,
    consensus_content TEXT NOT NULL,  -- Markdown content
    human_feedback JSONB,  -- Human corrections/additions
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document versions (for all project docs)
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    document_path VARCHAR(500) NOT NULL,  -- 'docs/ONBOARDING.md'
    version INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    change_summary TEXT,
    council_session_id UUID REFERENCES council_sessions(id),
    created_by VARCHAR(100),  -- 'council', 'human', 'agent'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.4 Sync Mechanism

```python
class DocumentSyncService:
    """Keeps MD files and database in sync."""

    async def save_council_result(
        self,
        project_id: int,
        document_type: str,
        consensus: CouncilConsensus,
        human_feedback: Optional[HumanFeedback] = None
    ):
        # 1. Save to database
        session = await self.db.create_council_session(
            project_id=project_id,
            document_type=document_type
        )

        for review in consensus.reviews:
            await self.db.save_review(session.id, review)

        await self.db.save_consensus(
            session.id,
            consensus.document,
            human_feedback
        )

        # 2. Write MD files
        project_path = f"Projecten/{project.name}"

        # Main document
        await self.write_md(
            f"{project_path}/docs/{document_type.upper()}.md",
            consensus.final_document
        )

        # Review history
        for i, review in enumerate(consensus.reviews, 1):
            await self.write_md(
                f"{project_path}/docs/reviews/{document_type}/round-{i}-review.md",
                review.to_markdown()
            )

        # Human feedback
        if human_feedback:
            await self.write_md(
                f"{project_path}/docs/reviews/{document_type}/human-feedback.md",
                human_feedback.to_markdown()
            )

        # 3. Update version history
        await self.db.create_version(
            project_id=project_id,
            document_path=f"docs/{document_type.upper()}.md",
            content=consensus.final_document,
            council_session_id=session.id
        )
```

---

## 5. Document Templates per Type

### 5.1 ONBOARDING.md Template

```markdown
---
document_type: onboarding
version: 1
council_verified: true
council_session: abc123
last_updated: 2025-11-26
approved_by: eddie
---

# {Project Name} - Developer Onboarding

## Project Purpose
{2 zinnen: wat het IS en wat het NIET is}

## Architecture
{Pattern + layer beschrijving met concrete paths}

## Quick Start
```bash
{3 commands max}
```

## Code Locations
{Feature → file mapping}

## Current Status
{Wat is af, wat is de next priority}

## Pro Tips
{Debugging, troubleshooting, common pitfalls}

---
*This document was generated via LLM Council and verified by a human reviewer.*
*Council session: {session_id} | Approved: {date}*
```

### 5.2 ADR Template

```markdown
---
document_type: adr
adr_number: 001
title: {Decision Title}
status: proposed|accepted|deprecated|superseded
council_verified: false
---

# ADR-{number}: {Title}

## Status
{proposed | accepted | deprecated | superseded by ADR-XXX}

## Context
{Why is this decision needed?}

## Decision
{What did we decide?}

## Consequences
{Positive and negative consequences}

## Alternatives Considered
{What other options were evaluated?}
```

### 5.3 ARCHITECTURE.md Template

```markdown
---
document_type: architecture
version: 1
council_verified: true
---

# {Project Name} - Architecture

## Overview
{High-level system description}

## System Context
{C4 Level 1 - System Context}

## Container View
{C4 Level 2 - Containers/Services}

## Component View
{C4 Level 3 - Key Components}

## Technology Stack
{Languages, frameworks, databases}

## Quality Attributes
{Performance, Security, Scalability decisions}

## Constraints
{Technical and business constraints}
```

---

## 6. API Endpoints voor Human Review

```python
# backend/app/api/council_review.py

@router.get("/council/sessions/{project_id}")
async def list_council_sessions(project_id: int):
    """List all council sessions for a project."""

@router.get("/council/sessions/{session_id}/review")
async def get_review_interface(session_id: UUID):
    """Get all data needed for human review UI."""
    return {
        "consensus_draft": ...,
        "provider_contributions": [
            {
                "provider": "ollama/qwen2.5-coder:7b",
                "score": 35,
                "correct_items": [...],
                "incorrect_items": [...],
            },
            ...
        ],
        "conflicts": [...],
        "missing_info_placeholder": "",
        "nuances_placeholder": "",
    }

@router.post("/council/sessions/{session_id}/human-feedback")
async def submit_human_feedback(
    session_id: UUID,
    feedback: HumanFeedbackRequest
):
    """Submit human feedback and trigger re-synthesis."""

@router.post("/council/sessions/{session_id}/approve")
async def approve_consensus(session_id: UUID):
    """Approve final consensus and save to project."""
```

---

## 7. Implementatie Roadmap

| Week | Task | Deliverable |
|------|------|-------------|
| **Week 55** | Database schema uitbreiding | council_* tables |
| **Week 55** | DocumentSyncService | MD ↔ DB sync |
| **Week 56** | Human Review UI | Frontend component |
| **Week 56** | API endpoints | Council review API |
| **Week 57** | Project template migration | Bestaande projecten updaten |
| **Week 57** | Testing & Documentation | E2E tests + docs |

---

## 8. Conclusie

### Voordelen van deze aanpak

1. **Single Source of Truth per project** - Alle docs op vaste plek
2. **Council-verified quality** - Multi-LLM peer review
3. **Human oversight** - Final approval door developer
4. **Queryable history** - Alle versies in database
5. **Git-friendly** - MD files voor version control
6. **API access** - Dashboards kunnen docs tonen

### Next Steps

1. Review dit voorstel
2. Feedback van team
3. Prioritering in roadmap
4. Begin met database schema

---

**Status**: Awaiting Review
**Author**: AI Agent Platform
**Related**: [LLM Council Review](../reviews/LLM_COUNCIL_ONBOARDING_REVIEW.md)
