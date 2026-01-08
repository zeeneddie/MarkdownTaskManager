# Gestandaardiseerde Project Workflows

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 69 COMPLETE
**Last Updated:** 2025-12-17

---

## Overview

3 gestandaardiseerde workflows voor consistente project analyse en migratie:

1. **Project Analyse** (Standalone) - Legacy health check
2. **Migratie Planning** (Vereist Workflow 1) - Planning na analyse
3. **Volledig** (Beide) - Complete assessment

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GESTANDAARDISEERDE PROJECT WORKFLOWS                       │
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │  WORKFLOW 1: PROJECT ANALYSE (Standalone)                              │  │
│   │  ─────────────────────────────────────────                             │  │
│   │  INPUT: Source code directory                                          │  │
│   │  OUTPUT: Project Health Report                                         │  │
│   │                                                                         │  │
│   │  Fasen:                                                                 │  │
│   │  1. Registratie      → ApplicationRegistry scan                        │  │
│   │  2. AS-IS Analyse    → Miguel: huidige architectuur                    │  │
│   │  3. Code Analyse     → CodeRAG: patterns, dependencies                 │  │
│   │  4. Security Scan    → Quinn: OWASP Top 10 vulnerabilities             │  │
│   │  5. Quality Audit    → Quinn: tech debt, code smells                   │  │
│   │  6. Health Report    → Diana: comprehensive report                     │  │
│   │                                                                         │  │
│   │  RESULT: project_assessment record in database                         │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                       │                                       │
│                                       ▼                                       │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │  WORKFLOW 2: MIGRATIE ANALYSE + PLANNING                               │  │
│   │  ────────────────────────────────────────                              │  │
│   │  PREREQUISITE: Completed Workflow 1 (assessment_id required)           │  │
│   │                                                                         │  │
│   │  INPUT: assessment_id + target_technology                              │  │
│   │  OUTPUT: Migration Plan                                                │  │
│   │                                                                         │  │
│   │  Fasen:                                                                 │  │
│   │  7. FP Estimation    → Eliza: IFPUG function points                    │  │
│   │  8. Target Arch      → Felix: architecture recommendation              │  │
│   │  9. Migration Plan   → Felix: strategy, phases, timeline               │  │
│   │  10. Final Report    → Diana: comprehensive migration plan             │  │
│   │                                                                         │  │
│   │  RESULT: migration_plan record linked to assessment                    │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │  WORKFLOW 3: VOLLEDIG (Analyse + Migratie)                             │  │
│   │  ─────────────────────────────────────────                             │  │
│   │  INPUT: Source code directory + target_technology                      │  │
│   │  OUTPUT: Complete Assessment + Migration Plan                          │  │
│   │                                                                         │  │
│   │  Uitvoering: Workflow 1 → automatisch → Workflow 2                     │  │
│   │                                                                         │  │
│   │  RESULT: Beide records in één doorloop                                 │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Rollen per Workflow

| Fase | Agent | Specialiteit | Output |
|------|-------|--------------|--------|
| Registratie | ApplicationRegistry | Stack detectie | application record |
| AS-IS Analyse | Miguel | Huidige architectuur | architecture_analysis |
| Code Analyse | CodeRAG | Patterns, dependencies | code_analysis |
| Security | Quinn | OWASP vulnerabilities | security_findings |
| Quality | Quinn | Tech debt, code smells | quality_report |
| Health Report | Diana | Documentatie | health_report.md |
| FP Estimation | Eliza | IFPUG schattingen | fp_estimation |
| Target Arch | Felix | Architectuur design | architecture_recommendation |
| Migration Plan | Felix | Strategie, fases | migration_plan |
| Final Report | Diana | Volledige documentatie | migration_report.md |

---

## Database Schema

### Project Assessments (Workflow 1 output)

```sql
CREATE TABLE project_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id INTEGER REFERENCES applications(id),
    assessment_date TIMESTAMP DEFAULT NOW(),

    -- AS-IS Architecture (Miguel)
    as_is_architecture JSONB,        -- Huidige architectuur
    architecture_pattern VARCHAR(50), -- detected pattern

    -- Code Analysis (CodeRAG)
    code_analysis JSONB,             -- Patterns, dependencies
    line_count INTEGER,
    file_count INTEGER,

    -- Security (Quinn)
    security_findings JSONB,         -- OWASP vulnerabilities
    security_risk_score INTEGER,     -- 0-100
    security_grade VARCHAR(1),       -- A-F

    -- Quality (Quinn)
    quality_report JSONB,            -- Tech debt, code smells
    quality_score INTEGER,           -- 0-100
    quality_grade VARCHAR(1),        -- A-F

    -- Overall
    overall_health_score INTEGER,    -- 0-100
    overall_grade VARCHAR(1),        -- A-F

    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Migration Plans (Workflow 2 output)

```sql
CREATE TABLE migration_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES project_assessments(id) NOT NULL,

    -- Target (input)
    target_technology VARCHAR(50) NOT NULL,

    -- FP Estimation (Eliza)
    unadjusted_fp INTEGER,
    adjusted_fp INTEGER,
    vaf DECIMAL(3,2),
    total_hours INTEGER,
    total_days INTEGER,

    -- Architecture (Felix)
    target_architecture JSONB,
    architecture_pattern VARCHAR(50),
    migration_strategy VARCHAR(50),  -- strangler_fig, big_bang, etc.
    architecture_decisions JSONB,    -- ADRs

    -- Planning (Felix)
    phases JSONB,                    -- Migration phases
    timeline_weeks INTEGER,
    team_size_recommended INTEGER,

    -- Risks
    risks JSONB,
    blockers JSONB,

    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Workflow 1: Project Analyse

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/project-assessment/start` | POST | Start nieuwe analyse |
| `/api/project-assessment/{id}` | GET | Status van lopende analyse |
| `/api/project-assessment/{id}/as-is` | GET | AS-IS architectuur (Miguel) |
| `/api/project-assessment/{id}/security` | GET | Security findings (Quinn) |
| `/api/project-assessment/{id}/quality` | GET | Quality report (Quinn) |
| `/api/project-assessment/{id}/report` | GET | Complete health report |
| `/api/project-assessments` | GET | Alle assessments |

### Workflow 2: Migratie Planning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/migration-plan/start` | POST | Start migratie planning (requires assessment_id) |
| `/api/migration-plan/{id}` | GET | Status van planning |
| `/api/migration-plan/{id}/estimation` | GET | FP estimation (Eliza) |
| `/api/migration-plan/{id}/architecture` | GET | Target architecture (Felix) |
| `/api/migration-plan/{id}/phases` | GET | Migration phases |
| `/api/migration-plan/{id}/report` | GET | Complete migration plan |
| `/api/migration-plans` | GET | Alle migratie plannen |

### Workflow 3: Volledig

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/full-assessment/start` | POST | Start complete workflow |
| `/api/full-assessment/{id}` | GET | Status beide workflows |
| `/api/full-assessment/{id}/report` | GET | Combined report |

---

## Green Paper vs Brown Paper

### Dual-Path Onboarding

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECT ONBOARDING                                   │
│                                                                              │
│   ┌───────────────────────────────┐   ┌───────────────────────────────┐     │
│   │         GREEN PAPER           │   │         BROWN PAPER           │     │
│   │      (Business-First)         │   │      (Code-First)             │     │
│   │                               │   │                               │     │
│   │  INPUT:                       │   │  INPUT:                       │     │
│   │  • Stakeholder vragen         │   │  • Source code scan           │     │
│   │  • Business requirements      │   │  • Existing documentation     │     │
│   │  • Product vision             │   │  • Database schema            │     │
│   │                               │   │  • API endpoints              │     │
│   │  PROCESS:                     │   │                               │     │
│   │  1. Peter: 6 BMAD vragen      │   │  PROCESS:                     │     │
│   │  2. Peter: Constitution       │   │  1. Scan: Detect stacks       │     │
│   │  3. Felix: Specification      │   │  2. Analyze: Extract domains  │     │
│   │  4. Felix: Epic breakdown     │   │  3. Synthesize: Constitution  │     │
│   │                               │   │  4. Generate: Epic breakdown  │     │
│   │  USE CASE:                    │   │                               │     │
│   │  • New projects (greenfield)  │   │  USE CASE:                    │     │
│   │  • Clear requirements         │   │  • Legacy projects            │     │
│   │                               │   │  • Code without docs          │     │
│   └───────────────┬───────────────┘   └───────────────┬───────────────┘     │
│                   │                                   │                      │
│                   └─────────────┬─────────────────────┘                      │
│                                 ↓                                            │
│              ┌─────────────────────────────────────────┐                     │
│              │          UNIFIED OUTPUT                 │                     │
│              │                                         │                     │
│              │  📜 Constitution (missie, principes)    │                     │
│              │  📋 Specification (architectuur, specs) │                     │
│              │  🎯 Epics (grote functionele gebieden)  │                     │
│              │  ⭐ Features (concrete features)        │                     │
│              │  📖 Stories (user stories)              │                     │
│              │  ✅ Tasks (technische taken)            │                     │
│              └─────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Green Paper (6 BMAD Questions)

```python
BMAD_QUESTIONS = [
    "Wat is het primaire doel van dit project?",
    "Wie zijn de belangrijkste stakeholders?",
    "Wat zijn de kritieke succesfactoren?",
    "Wat zijn de belangrijkste risico's?",
    "Wat zijn de technische constraints?",
    "Wat is de gewenste timeline?"
]
```

### Brown Paper (8 BMAD Questions)

```python
BROWN_PAPER_QUESTIONS = [
    "Wat zijn de huidige pijnpunten van dit legacy systeem?",
    "Welke businesswaarde moet behouden blijven?",
    "Wat zijn de technische constraints voor migratie?",
    "Wie zijn de kennisdragers van dit systeem?",
    "Wat is het budget/timeline voor modernisering?",
    "Welke integraties moeten behouden blijven?",
    "Wat is de gewenste target architectuur?",
    "Welke risico's zien stakeholders?"
]
```

---

## Use Cases

| Scenario | Workflow | Voorbeeld |
|----------|----------|-----------|
| Legacy project health check | 1 | "Hoe gezond is dit VB.NET project?" |
| Tech debt inventarisatie | 1 | "Wat zijn de kwaliteitsproblemen?" |
| Security audit | 1 | "Welke security issues zijn er?" |
| Migratie planning (na analyse) | 2 | "Plan migratie naar Python/FastAPI" |
| Complete project assessment | 3 | "Analyseer en plan migratie in één keer" |
| Nieuwe klant onboarding | 3 | "Scan project en maak offerte" |

---

## Benefits

- **Consistentie**: Elke analyse volgt dezelfde stappen
- **Vergelijkbaar**: Resultaten tussen projecten zijn vergelijkbaar
- **Flexibiliteit**: Alleen analyse, alleen migratie, of beide
- **Traceability**: Prerequisites enforced (migratie vereist analyse)

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [deep-extraction-pipeline.md](./deep-extraction-pipeline.md) - Multi-LLM extraction
- [layered-analysis.md](./layered-analysis.md) - Layered Analysis Service
