# Migration Enhanced Workflow

**Versie:** 1.0
**Datum:** 2025-12-30
**Status:** PLANNED (Week 129-130)
**Fase:** 21

---

## Overview

De Migration Enhanced workflow is de **uitvoerings-workflow** die de output van Brown Paper Enhanced als input neemt en de daadwerkelijke migratie uitvoert.

### Workflow Scheiding

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    ANALYSE vs UITVOERING                                        │
│                                                                                 │
│  ┌─────────────────────────────┐         ┌─────────────────────────────┐       │
│  │   BROWN_PAPER_ENHANCED      │         │   MIGRATION_ENHANCED        │       │
│  │   (Fase 20 - Week 128)      │         │   (Fase 21 - Week 129)      │       │
│  │                             │         │                             │       │
│  │   Focus: ANALYSE            │ ──────► │   Focus: UITVOERING         │       │
│  │   Output: Specificatie      │         │   Input: Brown Paper Output │       │
│  │                             │         │   Output: Gemigreerde App   │       │
│  └─────────────────────────────┘         └─────────────────────────────┘       │
│                                                                                 │
│  6 Phases:                               7 Phases:                              │
│  1. Code Understanding                   1. Preparation                         │
│  2. Domain Extraction                    2. Code Transformation                 │
│  3. Hierarchical Extraction              3. Data Migration                      │
│  4. Deep Extraction                      4. Testing                             │
│  5. Estimation                           5. Validation                          │
│  6. Output                               6. Acceptance                          │
│                                          7. Deployment                          │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Input: Brown Paper Enhanced Output

De Migration Enhanced workflow verwacht de volgende input van een voltooide Brown Paper Enhanced sessie:

### Required Input

| Field | Source | Description |
|-------|--------|-------------|
| `session_id` | Brown Paper | Koppeling naar analyse sessie |
| `dependency_graph` | Phase 1 | Module afhankelijkheden, circular deps |
| `code_analysis` | Phase 1 | Complexity metrics, coupling, cohesion |
| `layered_analysis` | Phase 1 | VBScript, stored procs, ASP patterns |
| `domains` | Phase 2 | Business domains, CAFCR mapping |
| `hierarchy` | Phase 3 | Epic/Feature/Story/Task structuur |
| `deep_extraction` | Phase 4 | Business rules, conflicts, confidence |
| `estimation` | Phase 5 | FP, SP, effort, risk assessment |
| `target_technology` | Config | Target stack (dotnet8, python_fastapi, etc.) |
| `migration_strategy` | Config | strangler_fig, big_bang, phased, etc. |

### Input Validation

```python
class MigrationEnhancedRequest:
    brown_paper_session_id: str  # Required - link to analysis
    target_technology: TargetTechnology
    target_database: TargetDatabase
    migration_strategy: MigrationStrategy
    team_size: int = 3

    # Optional overrides
    skip_phases: List[int] = []
    parallel_execution: bool = True
    test_strategy: TestStrategy = TestStrategy.AUTO  # AUTO, MIGRATE, GENERATE
```

---

## 7-Phase Workflow

### Phase Overview

```
Time →  ════════════════════════════════════════════════════════════════════►

Phase 1: [████████]
Phase 2:          [████████████████████████]
Phase 3:          [████████████████████████]  ← Parallel met Phase 2
Phase 4:          [████████████████████████]  ← Parallel met Phase 2+3
Phase 5:                                    [████████]
Phase 6:                                             [████████]
Phase 7:                                                      [████████]

GATE: Phase 2+3+4 MOETEN allemaal DONE zijn voordat Phase 5 start
```

---

## Phase 1: Preparation

**Agent:** Miguel (Migration Architect)
**Duration:** 1-2 dagen
**Parallel:** Nee (moet eerst)

### Taken

| Task | Description | Output |
|------|-------------|--------|
| **Environment Setup** | Target stack installatie, dev environment | `environment_ready: bool` |
| **Tooling Configuration** | Ora2Pg, SQLines, converters configureren | `tools_configured: List[Tool]` |
| **Brown Paper Import** | Session laden, context valideren | `brown_paper_loaded: bool` |
| **Workspace Creation** | Git repos, branches, CI/CD skeleton | `workspace_url: str` |
| **Team Assignment** | Resources alloceren per phase | `team_assignments: Dict` |

### Exit Criteria

- [ ] Target environment draait
- [ ] Alle tools geconfigureerd en getest
- [ ] Brown Paper data gevalideerd en geladen
- [ ] Git repository met branch strategy
- [ ] CI/CD pipeline skeleton

### API

```
POST /api/migration/{session_id}/start
GET  /api/migration/{session_id}/phase/1/status
```

---

## Phase 2: Code Transformation

**Agent:** Miguel + Felix
**Duration:** 2-6 weken (afhankelijk van LOC)
**Parallel:** Ja (met Phase 3 en 4)

### Taken

| Task | Description | Input |
|------|-------------|-------|
| **Automatic Conversion** | Ora2Pg, SQLines batch processing | `layered_analysis.files` |
| **Pattern Mapping** | Legacy → Modern architecture patterns | `code_analysis.patterns` |
| **Component Migration** | Per module transformatie | `hierarchy.features` |
| **Manual Fixes** | Edge cases, complex logic | `deep_extraction.conflicts` |
| **Code Review** | Quality check per component | Transformed code |

### Pattern Mapping Table

| Legacy Pattern | Target: .NET 8 | Target: Python FastAPI | Target: Node NestJS |
|----------------|----------------|------------------------|---------------------|
| VB6 Form | Blazor Component | React Component | Angular Component |
| ASP Classic | Razor Page | Jinja2 Template | EJS Template |
| ADO Recordset | EF Core DbSet | SQLAlchemy Model | TypeORM Entity |
| VBScript Class | C# Class | Python Class | TypeScript Class |
| Stored Procedure | EF Core Raw SQL | SQLAlchemy text() | Raw Query |

### Exit Criteria

- [ ] Alle modules getransformeerd
- [ ] Geen compiler/syntax errors
- [ ] Code review completed
- [ ] Pattern compliance verified

### API

```
POST /api/migration/{session_id}/phase/2/start
GET  /api/migration/{session_id}/phase/2/progress
GET  /api/migration/{session_id}/phase/2/components
```

---

## Phase 3: Data Migration

**Agent:** Miguel
**Duration:** 1-3 weken
**Parallel:** Ja (met Phase 2 en 4)

### Taken

| Task | Description | Tools |
|------|-------------|-------|
| **Schema Migration** | DDL conversie, indexes, constraints | Ora2Pg, SQLines |
| **Data Transfer** | ETL pipeline, batch processing | Custom ETL |
| **Stored Procedures** | PL/SQL → T-SQL/Python conversie | Manual + LLM |
| **Triggers & Views** | Logica migreren of refactoren | Manual |
| **Data Validation** | Record counts, checksums | Validation scripts |

### Database Mapping

| Source | Target Options |
|--------|----------------|
| Oracle | PostgreSQL, SQL Server, MySQL |
| SQL Server | PostgreSQL, MySQL |
| MySQL | PostgreSQL |
| Access | SQLite, PostgreSQL |

### Exit Criteria

- [ ] Schema 100% gemigreerd
- [ ] Data 100% getransfereerd
- [ ] Foreign keys intact
- [ ] Stored procedures werkend
- [ ] Data validation passed

### API

```
POST /api/migration/{session_id}/phase/3/start
GET  /api/migration/{session_id}/phase/3/tables
GET  /api/migration/{session_id}/phase/3/validation
```

---

## Phase 4: Testing

**Agent:** Tessa (Test Engineer)
**Duration:** 2-4 weken
**Parallel:** Ja (met Phase 2 en 3) - **KRITIEK: moet klaar zijn als migratie klaar is**

### Test Strategy Decision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAP 1: Test Strategie Beslissing                                           │
│                                                                              │
│  Analyse van Brown Paper input:                                              │
│  • legacy_test_count: int                                                    │
│  • legacy_test_coverage: float                                               │
│  • legacy_test_framework: str                                                │
│  • test_quality_score: int (0-100)                                           │
│                                                                              │
│  ┌─────────────────────────┐         ┌─────────────────────────┐            │
│  │  Score >= 60            │         │  Score < 60             │            │
│  │                         │         │                         │            │
│  │  STRATEGY: MIGRATE      │         │  STRATEGY: GENERATE     │            │
│  │  Bestaande tests        │         │  Nieuwe tests van       │            │
│  │  converteren + aanvullen│         │  Brown Paper specs      │            │
│  └─────────────────────────┘         └─────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Strategy A: Test Migration (Score >= 60)

| Task | Description |
|------|-------------|
| **Framework Conversion** | NUnit → xUnit, JUnit → pytest, MSTest → xUnit |
| **Mock/Stub Migration** | Moq → NSubstitute, Mockito → pytest-mock |
| **Fixture Migration** | Database fixtures, test data |
| **Assertion Update** | Assert syntax aanpassen |
| **CI/CD Integration** | Pipeline configuratie |

### Strategy B: Test Generation (Score < 60)

| Input Source | Test Type Generated |
|--------------|---------------------|
| `hierarchy.stories[].acceptance_criteria` | Unit Tests |
| `hierarchy.features[].requirements` | Integration Tests |
| `hierarchy.epics[].critical_paths` | E2E Tests |
| `deep_extraction.business_rules` | Business Rule Tests |
| `code_analysis.complexity_hotspots` | Edge Case Tests |

### Test Completering (ALTIJD)

Ongeacht strategie, de volgende tests worden altijd toegevoegd:

| Category | Coverage Target | Source |
|----------|-----------------|--------|
| **Security Tests** | OWASP Top 10 | GhostCrew output |
| **Performance Tests** | Critical paths | Brown Paper hotspots |
| **Edge Cases** | High complexity areas | Code analysis |
| **Regression Suite** | All business rules | Deep extraction |

### Exit Criteria

- [ ] Test suite GROEN (100% passing)
- [ ] Coverage >= 80%
- [ ] Geen blocker/critical defects
- [ ] CI/CD pipeline actief
- [ ] Test rapport gegenereerd

### API

```
POST /api/migration/{session_id}/phase/4/start
GET  /api/migration/{session_id}/phase/4/strategy
GET  /api/migration/{session_id}/phase/4/coverage
GET  /api/migration/{session_id}/phase/4/results
```

---

## Phase 5: Validation

**Agent:** Quinn (Quality Inspector)
**Duration:** 1-2 weken
**Parallel:** Nee (wacht op Phase 2+3+4)

### Gate Check

```python
def can_start_phase_5(session: MigrationSession) -> bool:
    return (
        session.phase_2_status == "completed" and
        session.phase_3_status == "completed" and
        session.phase_4_status == "completed" and
        session.phase_4_tests_passing == True and
        session.phase_4_coverage >= 0.80
    )
```

### 5.1 Functional Equivalence

| Method | Description | Use Case |
|--------|-------------|----------|
| **Golden Master** | Snapshot vergelijking van outputs | Batch processing |
| **Parallel Run** | Beide systemen live, output diff | Real-time systems |
| **Sampling** | Random subset van transacties | High-volume systems |

```
Legacy System              New System
     │                          │
     ▼                          ▼
┌─────────┐                ┌─────────┐
│ Input A │────────────────│ Input A │
└─────────┘                └─────────┘
     │                          │
     ▼                          ▼
┌──────────┐               ┌──────────┐
│ Output A │      ==       │ Output A │  ✓ Match
└──────────┘               └──────────┘
```

### 5.2 Data Integrity

| Check | Method | Tolerance |
|-------|--------|-----------|
| Record Counts | COUNT(*) comparison | 0% |
| Checksums | MD5/SHA256 per table | 0% |
| Foreign Keys | Constraint validation | 0% |
| Null Patterns | NULL count comparison | 0% |
| Date/Time | Format validation | 0% |

### 5.3 Performance Baseline

| Metric | Measurement | Tolerance |
|--------|-------------|-----------|
| Response Time P50 | API latency | <= 110% of legacy |
| Response Time P95 | API latency | <= 120% of legacy |
| Response Time P99 | API latency | <= 150% of legacy |
| Throughput | Requests/second | >= 90% of legacy |
| Memory Usage | Peak memory | <= 120% of legacy |
| Database Queries | Query time | <= 110% of legacy |

### 5.4 Security Audit

| Category | Checks |
|----------|--------|
| **OWASP Top 10** | Injection, XSS, CSRF, etc. |
| **Authentication** | Token handling, session management |
| **Authorization** | Role-based access, permission checks |
| **Data Protection** | Encryption at rest/transit |
| **Secrets Management** | No hardcoded credentials |

### Exit Criteria

- [ ] 100% functional equivalence (of gedocumenteerde afwijkingen)
- [ ] 100% data integrity
- [ ] Performance binnen tolerantie
- [ ] Geen critical security issues
- [ ] Validation rapport gegenereerd

### API

```
POST /api/migration/{session_id}/phase/5/start
GET  /api/migration/{session_id}/phase/5/equivalence
GET  /api/migration/{session_id}/phase/5/integrity
GET  /api/migration/{session_id}/phase/5/performance
GET  /api/migration/{session_id}/phase/5/security
```

---

## Phase 6: Acceptance

**Agent:** Peter (Product Owner)
**Duration:** 3-5 dagen
**Parallel:** Nee

### Taken

| Task | Description | Source |
|------|-------------|--------|
| **Business Rule Verification** | Alle rules uit Brown Paper | `deep_extraction.business_rules` |
| **User Acceptance Testing** | Stories acceptance criteria | `hierarchy.stories[].acceptance_criteria` |
| **Stakeholder Demo** | Functionele demonstratie | N/A |
| **Sign-off Collection** | Go/No-Go beslissing | N/A |

### Acceptance Checklist

```markdown
## Business Rules Verification
- [ ] Rule 1: {description} - PASS/FAIL
- [ ] Rule 2: {description} - PASS/FAIL
...

## User Stories Acceptance
- [ ] STORY-001: {title} - ACCEPTED/REJECTED
- [ ] STORY-002: {title} - ACCEPTED/REJECTED
...

## Stakeholder Sign-off
- [ ] Product Owner: _______________  Date: ___
- [ ] Technical Lead: _______________  Date: ___
- [ ] Business Sponsor: _____________ Date: ___

## Go/No-Go Decision
[ ] GO - Proceed to deployment
[ ] NO-GO - Issues to resolve: _______________
```

### Exit Criteria

- [ ] Alle business rules verified
- [ ] Alle stories accepted
- [ ] Stakeholder sign-off collected
- [ ] GO decision

### API

```
POST /api/migration/{session_id}/phase/6/start
GET  /api/migration/{session_id}/phase/6/checklist
POST /api/migration/{session_id}/phase/6/signoff
GET  /api/migration/{session_id}/phase/6/decision
```

---

## Phase 7: Deployment

**Agent:** Paul (Project Lead)
**Duration:** 1-3 dagen
**Parallel:** Nee

### Deployment Strategies

| Strategy | Description | Risk | Best For |
|----------|-------------|------|----------|
| **Blue-Green** | Twee identieke environments | Low | Zero-downtime required |
| **Canary** | Graduele rollout (1% → 10% → 100%) | Low | High-traffic systems |
| **Rolling** | Instance-by-instance update | Medium | Stateless services |
| **Big Bang** | Complete cutover | High | Small systems |

### Deployment Checklist

```markdown
## Pre-Deployment
- [ ] Backup legacy system
- [ ] Backup legacy database
- [ ] Notify stakeholders
- [ ] Prepare rollback scripts

## Staging Deployment
- [ ] Deploy to staging
- [ ] Smoke tests passing
- [ ] Performance validation
- [ ] Security scan

## Production Deployment
- [ ] Deploy to production
- [ ] Smoke tests passing
- [ ] Monitor error rates
- [ ] Monitor performance

## Post-Deployment
- [ ] Verify all endpoints
- [ ] Check data integrity
- [ ] Update DNS/routing
- [ ] Legacy system standby (rollback ready)

## Rollback Trigger Criteria
- Error rate > 5%
- Response time P95 > 200% baseline
- Data integrity issues
- Security incident
```

### Exit Criteria

- [ ] Production deployment successful
- [ ] All smoke tests passing
- [ ] Error rate < 1%
- [ ] Performance within baseline
- [ ] Rollback plan tested
- [ ] Legacy system in standby

### API

```
POST /api/migration/{session_id}/phase/7/staging
POST /api/migration/{session_id}/phase/7/production
POST /api/migration/{session_id}/phase/7/rollback
GET  /api/migration/{session_id}/phase/7/status
```

---

## Complete API Reference

### Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/migration/start` | POST | Start nieuwe migratie sessie |
| `/api/migration/{session_id}` | GET | Haal sessie status op |
| `/api/migration/{session_id}/cancel` | POST | Annuleer migratie |

### Phase Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/migration/{session_id}/phase/{n}/start` | POST | Start phase N |
| `/api/migration/{session_id}/phase/{n}/status` | GET | Phase N status |
| `/api/migration/{session_id}/phase/{n}/pause` | POST | Pauzeer phase N |
| `/api/migration/{session_id}/phase/{n}/resume` | POST | Hervat phase N |

### Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/migration/{session_id}/report` | GET | Volledige migratie rapport |
| `/api/migration/{session_id}/report/testing` | GET | Test rapport |
| `/api/migration/{session_id}/report/validation` | GET | Validatie rapport |
| `/api/migration/{session_id}/report/deployment` | GET | Deployment rapport |

---

## Integration with Brown Paper Enhanced

### Session Linking

```python
# Start migration from Brown Paper session
migration_request = MigrationEnhancedRequest(
    brown_paper_session_id="bp-session-123",
    target_technology=TargetTechnology.DOTNET8,
    target_database=TargetDatabase.POSTGRESQL,
    migration_strategy=MigrationStrategy.STRANGLER_FIG,
    team_size=4
)

migration_session = await migration_service.start(migration_request)
```

### Data Flow

```
Brown Paper Enhanced                    Migration Enhanced
┌─────────────────┐                    ┌─────────────────┐
│ Phase 1 Output  │───dependency_graph──►│ Phase 1: Prep   │
│                 │───code_analysis────►│                 │
│                 │───layered_analysis─►│                 │
├─────────────────┤                    ├─────────────────┤
│ Phase 2 Output  │───domains──────────►│ Phase 2: Code   │
│                 │───cafcr_mapping────►│                 │
├─────────────────┤                    ├─────────────────┤
│ Phase 3 Output  │───hierarchy────────►│ Phase 4: Test   │
│                 │                    │ (story specs)   │
├─────────────────┤                    ├─────────────────┤
│ Phase 4 Output  │───business_rules───►│ Phase 4: Test   │
│                 │───conflicts────────►│ Phase 5: Valid  │
├─────────────────┤                    ├─────────────────┤
│ Phase 5 Output  │───estimation───────►│ Phase 1: Prep   │
│                 │───risk_assessment──►│ (planning)      │
└─────────────────┘                    └─────────────────┘
```

---

## Agent Assignments

| Phase | Primary Agent | Supporting Agents | Responsibilities |
|-------|---------------|-------------------|------------------|
| **1. Preparation** | Miguel | Paul | Environment, tooling, planning |
| **2. Code Transformation** | Miguel | Felix | Conversion, patterns, quality |
| **3. Data Migration** | Miguel | - | Schema, data, procedures |
| **4. Testing** | Tessa | Quinn | Test strategy, coverage, CI/CD |
| **5. Validation** | Quinn | Tessa | Equivalence, integrity, security |
| **6. Acceptance** | Peter | Diana | Business rules, UAT, sign-off |
| **7. Deployment** | Paul | Miguel | Staging, production, rollback |

---

## Tier-Aware Execution

| Tier | Phases Included | Automation Level | Human Review |
|------|-----------------|------------------|--------------|
| **BASIC** | 1-4 | High | None |
| **STANDARD** | 1-5 | High | Optional Phase 5 |
| **PROFESSIONAL** | 1-6 | Medium | Phase 5+6 |
| **PREMIUM** | 1-7 | Low | All phases |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Migration Completion** | 100% | All phases completed |
| **Test Coverage** | >= 80% | Phase 4 output |
| **Functional Equivalence** | 100% | Phase 5 output |
| **Data Integrity** | 100% | Phase 5 output |
| **Performance Baseline** | <= 110% | Phase 5 output |
| **Security Issues** | 0 critical | Phase 5 output |
| **Acceptance Rate** | 100% | Phase 6 output |
| **Deployment Success** | 100% | Phase 7 output |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Brown Paper Enhanced](./brown-paper-enhanced.md) | Analysis workflow (input) |
| [Migration Analyzer](./migration-analyzer-specification.md) | Code analysis tools |
| [Migration Framework V2](./migration-framework-v2-technical-spec.md) | Technical specifications |
| [GhostCrew Security](./ghostcrew-security.md) | Security scanning |
| [Deep Extraction Pipeline](./deep-extraction-pipeline.md) | Story extraction |

---

## Implementation Plan

### Week 129

| Day | Tasks |
|-----|-------|
| 1-2 | Create `migration_enhanced.py` models |
| 3-4 | Implement Phase 1-2 service methods |
| 5 | Implement Phase 3 service methods |

### Week 130

| Day | Tasks |
|-----|-------|
| 1-2 | Implement Phase 4-5 service methods |
| 3 | Implement Phase 6-7 service methods |
| 4 | Add API endpoints |
| 5 | Create tests, documentation updates |

---

**Author:** Claude Opus 4.5
**Review:** Pending
**Approval:** Pending
