# MarkdownTaskManager - Kernfunctionaliteit & Architectuur

**Versie:** 1.0
**Datum:** 15 november 2025
**Status:** Architectuur Definitie

---

## 1. MISSIE

MarkdownTaskManager is een **agentic project management platform** dat software ontwikkeling, onderhoud, migratie en kwaliteitscontrole volledig kan automatiseren door middel van gespecialiseerde AI-agents.

Het platform kan zowel **eigen projecten** als **externe codebases** beheren, analyseren, onderhouden en transformeren.

---

## 2. KERNFUNCTIONALITEIT

### 2.1 Zeven Primaire Capabilities

MarkdownTaskManager kan de volgende operaties volledig autonoom uitvoeren:

#### 1️⃣ **Nieuwe Projecten Uitvoeren**
**Doel:** Van idee naar werkende software
**Input:** Project omschrijving, requirements, tech stack keuzes
**Output:** Volledig geïmplementeerd project met tests, documentatie en deployment

**Workflow:**
- Specificatie generatie (/constitution → /specify → /plan)
- Architectuur ontwerp (technische keuzes, patterns)
- Epic → Feature → Story → Task breakdown
- Automatische code generatie via agents
- Test suite generatie en uitvoering
- Documentatie schrijven
- Deployment configuratie

**Voorbeeld:** "Bouw een payment processing systeem met Stripe" → Volledig werkend systeem in 3-5 sprints

---

#### 2️⃣ **Projecten Onderhouden**
**Doel:** Bestaande projecten gezond en actueel houden
**Input:** Project repository (eigen beheerde projecten)
**Output:** Up-to-date dependencies, opgeloste security issues, gerefactorde code

**Workflow:**
- Dependency scan (npm audit, pip-audit)
- Security vulnerability detection (Snyk, OWASP ZAP)
- Code smell detection (SonarQube)
- Automated updates met test validatie
- Refactoring van technical debt
- Performance optimalisatie

**Voorbeeld:** Maandelijkse maintenance run op alle actieve projecten

---

#### 3️⃣ **Software Elders Geschreven Onderhouden**
**Doel:** Externe codebases beheren zonder volledige ownership
**Input:** Toegang tot externe repository (GitHub, GitLab, Bitbucket)
**Output:** Maintenance pull requests, issue fixes, dependency updates

⚠️ **BELANGRIJKE WORKFLOW DEPENDENCY:**
> **Bij externe repositories wordt ALTIJD eerst een Kwaliteitsonderzoek (#4) uitgevoerd**
> Dit zorgt voor baseline metrics en identificeert kritieke issues voordat maintenance begint.

**2-Phase Workflow:**

**Phase 1: Quality Audit (VERPLICHT)**
- Volledige quality audit uitvoeren (zie capability #4)
- Baseline metrics vastleggen:
  - Technical Debt Ratio (TDR)
  - Security vulnerabilities
  - Test coverage
  - Performance metrics
- Prioritized findings genereren
- Maintenance scope bepalen

**Phase 2: Maintenance Execution**
- Repository clone en analyse
- Automated dependency updates (op basis van audit findings)
- Security patch applicatie (prioritized by audit)
- Bug fix detectie en resolutie
- Code quality improvements (target: TDR reduction)
- Pull request generatie met audit referenties

**Output:**
- Initial audit report (baseline)
- Maintenance pull requests met voor/na metrics
- Progress tracking tegen baseline
- Updated documentation

**Voorbeeld:**
- 32 legacy repositories voor migratie voorbereiding
- Eerst: Audit alle 32 repos → baseline TDR 18% gemiddeld
- Daarna: Maintenance → reduce TDR naar 12% before migration start

---

#### 4️⃣ **Kwaliteitsonderzoeken Doen**
**Doel:** Diepgaande analyse van code quality, security en performance
**Input:** Codebase + audit scope (security, performance, architecture)
**Output:** Gedetailleerd audit rapport met prioritized findings

**Workflow:**
- **Security Audit**
  - OWASP Top 10 vulnerability scan
  - Dependency vulnerability check
  - Authentication/authorization review
  - Data protection compliance (GDPR)

- **Performance Audit**
  - Response time analysis (p50, p95, p99)
  - Database query optimization (N+1 detection)
  - Frontend performance (Lighthouse)
  - Resource usage profiling

- **Code Quality Audit**
  - Cyclomatic complexity (<15 per function)
  - Code duplication detection
  - Test coverage analysis (target 80%)
  - Documentation completeness

- **Architecture Audit**
  - Design patterns compliance
  - Coupling/cohesion analysis
  - Scalability assessment
  - Technical debt measurement (TDR)

**Output Format:** Risk-prioritized remediation plan met effort estimates

**Voorbeeld:** Pre-production audit HCI EPD project → 147 findings, 23 critical

---

#### 5️⃣ **Software Migreren naar Nieuwe Tech Stack**
**Doel:** Legacy codebases moderniseren (taal, framework, platform)
**Input:** Source codebase + target tech stack
**Output:** Volledig gemigreerde codebase met validatie

**Migratie Types:**
- **Technology Migration:** Python 2→3, Vue 2→3, ASP Classic→.NET Core
- **Platform Migration:** On-prem→Cloud, Monolith→Microservices
- **Data Migration:** MySQL→PostgreSQL, SQL→NoSQL
- **Integration Migration:** REST→GraphQL, v1→v2 API

**5-Stage Workflow:**

**Stage 1: Assessment**
- Inventarisatie: wat moet migreren?
- Dependency mapping
- Risk assessment (data loss, downtime)
- Migration Complexity Index (MCI) berekening
  - MCI < 10: LOW (5 FP, 2-3 sprints)
  - MCI 10-50: MEDIUM (13 FP, 4-6 sprints)
  - MCI 50-200: HIGH (21 FP, 7-10 sprints)
  - MCI > 200: CRITICAL (34 FP, 11-15 sprints)

**Stage 2: Planning**
- Migration strategy (Big Bang / Phased / Parallel)
- Data mapping en transformation rules
- Timeline estimation (FPA + data volume)
- Rollback plan

**Stage 3: Execution**
- Incremental migration (batch processing)
- Automated code transformation (AST-based)
- Parallel execution met progress tracking
- Checkpoint/resume capability

**Stage 4: Validation**
- Data integrity checks (100% validation)
- Functional equivalence testing
- Performance benchmarking (≥90% baseline)
- Security validation

**Stage 5: Cutover**
- Pre-cutover checklist
- DNS/routing switch
- Post-cutover monitoring (48h)
- Rollback decision criteria (error rate >5%)

**Voorbeeld:** HCI EPD migratie (1.38M LOC ASP Classic → .NET Core) → 15 sprints

---

#### 6️⃣ **Kleine Features aan Projecten Uitvoeren**
**Doel:** Bestaande projecten uitbreiden met nieuwe functionaliteit
**Input:** Feature request + target project
**Output:** Geïmplementeerde feature met tests en documentatie

**Workflow:**
- Context analysis (begrijp bestaande implementatie)
- Extension point identificatie
- Design met backward compatibility
- Implementation (hergebruik bestaande patterns)
- Integration testing met bestaande features
- Documentation update

**Effort Multiplier:** 1.5x base feature SP (lager risico door bestaande tests/patterns)

**Voorbeeld:** "Add dark mode to existing dashboard" → 8 SP (vs 13 SP nieuwe feature)

---

#### 7️⃣ **Bugfixes Uitvoeren op Projecten**
**Doel:** Production issues, test failures en user reports oplossen
**Input:** Bug report + severity
**Output:** Fix met regression test binnen SLA

**Severity Classification:**
- **P0 (Critical):** Production down, data loss → 4 hours max
- **P1 (High):** Major feature broken → 1 day max
- **P2 (Medium):** Minor feature issues → 1 week max
- **P3 (Low):** Cosmetic, workaround exists → 2 weeks max
- **P4 (Trivial):** Nice-to-have → backlog

**Bug Fix Workflow:**
1. **Reproduction:** Create failing test (minimal reproducible example)
2. **Root Cause Analysis:** Stack trace, git bisect, debugging
3. **Fix Implementation:** Code fix + regression test
4. **Validation:** Full test suite + manual testing if needed
5. **Deployment:** Hotfix (P0/P1) of regular release (P2+)

**Voorbeeld:** P0 payment processing bug → fixed in 3h45m, hotfix deployed

---

## 3. WORK TYPE STREAMS

### 3.1 Overzicht Work Types

Elke capability wordt vertaald naar een **Work Type Stream** met gespecialiseerde workflow:

| # | Capability | Work Type | Primary Agent | Workflow | Dependencies |
|---|------------|-----------|---------------|----------|--------------|
| 1 | Nieuwe projecten uitvoeren | **NEW_FEATURE** | Feature Architect | Spec-Kit Pipeline | - |
| 2 | Projecten onderhouden | **MAINTENANCE** | Maintenance Specialist | 6-Stage Maintenance | - |
| 3 | Externe software onderhouden | **MAINTENANCE** + **QUALITY_AUDIT** | Quality Inspector → Maintenance Specialist | External Repo Mode (2-Phase) | ⚠️ **VERPLICHT: Eerst #4** |
| 4 | Kwaliteitsonderzoeken | **QUALITY_AUDIT** | Quality Inspector | SuperClaude Analyzer | - |
| 5 | Software migreren | **MIGRATION** | Migration Architect | 5-Stage Migration | - |
| 6 | Features uitvoeren | **ENHANCEMENT** | Enhancement Specialist | Simplified Spec-Kit | - |
| 7 | Bugfixes uitvoeren | **BUG** | Bug Hunter | Time-boxed Approach | - |

**Extra Work Types:**
- **QUALITY_IMPROVEMENT:** Technical debt reduction, refactoring
- **TESTING:** Test suite generatie en uitvoering

---

### 3.2 Shared Agent Pool

**Alle work type streams maken gebruik van dezelfde 8 gespecialiseerde agents:**

#### **Agent 1: Felix - Feature Architect** 🏗️
- **Role:** Design en specify nieuwe features
- **Execution:** Cloud (Claude Sonnet 4.5)
- **Tools:** spec-kit (/constitution, /specify, /plan, /tasks)
- **Triggers:** NEW_FEATURE, ENHANCEMENT

#### **Agent 2: Marcus - Maintenance Specialist** 🔧
- **Role:** Onderhoud en dependency updates
- **Execution:** Local (Ollama - DeepSeek Coder)
- **Tools:** code-maintenance-agent, npm audit, pip-audit
- **Triggers:** MAINTENANCE (eigen + externe projecten)

#### **Agent 3: Quinn - Quality Inspector** 🔍
- **Role:** Quality audits en security reviews
- **Execution:** Cloud (Claude met security personas)
- **Tools:** superclaude_framework (security/performance/architect personas)
- **Triggers:** QUALITY_AUDIT, QUALITY_IMPROVEMENT

#### **Agent 4: Betty - Bug Hunter** 🐛
- **Role:** Reproduce, diagnose en fix bugs
- **Execution:** Local (Ollama - Qwen 2.5)
- **Tools:** Debugger, logging, git bisect
- **Triggers:** BUG

#### **Agent 5: Eliza - Estimation Engine** 📊
- **Role:** Function Points en Story Points berekenen
- **Execution:** Local (Ollama - Llama 3.1) + ML model
- **Tools:** IFPUG calculator, Fibonacci mapper, historical data
- **Triggers:** Alle work types (post-breakdown)

#### **Agent 6: Tessa - Test Engineer** 🧪
- **Role:** Write en execute automated tests
- **Execution:** Local (Ollama - DeepSeek Coder)
- **Tools:** pytest, Jest, Playwright, Cucumber
- **Triggers:** TESTING, alle features (automated)

#### **Agent 7: Miguel - Migration Architect** 🚀
- **Role:** Plan en execute system migrations
- **Execution:** Cloud (GPT-4)
- **Tools:** Migration assessment, data transformation pipelines
- **Triggers:** MIGRATION

#### **Agent 8: Diana - Documentation Writer** 📝
- **Role:** Generate en maintain documentation
- **Execution:** Local (Ollama - Llama 3.1)
- **Tools:** Markdown generators, API doc tools (Swagger, JSDoc)
- **Triggers:** Alle work types (post-implementation)

---

### 3.3 Cross-Stream Agent Collaboration

**Voorbeeld: NEW_FEATURE workflow**
```
User Request: "Add payment processing with Stripe"
    ↓
[Felix] Feature Architect → Specificatie + breakdown
    ↓
[Eliza] Estimation Engine → 21 FP, 34 SP (Epic level)
    ↓
[Implementation Team] → Code generation
    ↓
[Tessa] Test Engineer → Test suite generatie
    ↓
[Quinn] Quality Inspector → Security review (payment = critical)
    ↓
[Diana] Documentation Writer → API docs, README update
```

**Voorbeeld: MIGRATION workflow**
```
Input: "Migrate HCI EPD (1.38M LOC ASP Classic → .NET Core)"
    ↓
[Miguel] Migration Architect → Assessment (MCI=185, HIGH)
    ↓
[Eliza] Estimation Engine → 21 FP, 15 sprints
    ↓
[Miguel] Migration Architect → Planning (Phased approach)
    ↓
[Marcus] Maintenance Specialist → Pre-migration cleanup
    ↓
[Execution] Incremental migration (batch processing)
    ↓
[Tessa] Test Engineer → Validation tests
    ↓
[Quinn] Quality Inspector → Post-migration audit
    ↓
[Diana] Documentation Writer → Migration report
```

---

## 4. UNIFIED ARCHITECTURE

### 4.1 Eight-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 8: KNOWLEDGE BASE                                    │
│  - Organizational knowledge (Supermemory - optional)        │
│  - Historical data & lessons learned                        │
│  - Cross-project learnings                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 7: QUALITY GATES                                      │
│  - Automated validation checkpoints                         │
│  - Security scans, test coverage, performance benchmarks    │
│  - Compliance checks (GDPR, NEN7510)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: WORK TYPE HANDLERS (8 Specialized Workflows)      │
│  - NEW_FEATURE: Spec-Kit Pipeline                          │
│  - MAINTENANCE: 6-Stage Maintenance Workflow               │
│  - MIGRATION: 5-Stage Migration Workflow                   │
│  - BUG: Time-boxed Bug Fix Workflow                        │
│  - QUALITY_AUDIT: SuperClaude Analyzer                     │
│  - ENHANCEMENT: Simplified Spec-Kit                        │
│  - QUALITY_IMPROVEMENT: Quality Pipeline                   │
│  - TESTING: 4-Track Testing Pipeline                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: DASHBOARD LAYER (Real-Time)                       │
│  - WebSocket-powered auto-refresh                           │
│  - Agent activity monitoring                                │
│  - Progress indicators & notifications                      │
│  - Multi-project view (eigen + externe repos)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: INTELLIGENCE LAYER                                │
│  - Function Point Calculator (IFPUG)                        │
│  - Story Point Estimator (Fibonacci + ML)                   │
│  - Risk Assessment Engine                                   │
│  - Confidence Interval Calculator                           │
│  - Migration Complexity Index (MCI)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: WORKFLOW LAYER                                    │
│  - Spec-Kit Pipeline: /constitution → /specify → /tasks     │
│  - Code-Maintenance-Agent: 6-stage maintenance             │
│  - Migration Workflows: 5-stage pipeline                   │
│  - BMAD-Method: Agentic project management                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: AGENT ORCHESTRATION                               │
│  - KaibanJS Framework (Multi-Agent Kanban)                  │
│  - 8 Specialized Agents (shared across all work types)     │
│  - Hybrid execution: Local (Ollama) + Cloud (Claude/GPT-4)  │
│  - Task queue with intelligent assignment                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: FOUNDATION LAYER                                  │
│  - Markdown Task Manager (Kanban Board) ✅                  │
│  - FastAPI Backend (45 endpoints) ✅                         │
│  - PostgreSQL Database (Hierarchical Schema) ✅              │
│  - Alembic Migrations ✅                                     │
│  - Multi-project repository management                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. EXECUTION MODES

### 5.1 Internal Project Mode
**Voor eigen beheerde projecten**
- Volledige controle over repository
- Direct push naar main/master
- Eigen workflow pipelines
- Continuous deployment

### 5.2 External Repository Mode
**Voor externe codebases (zoals HCI EPD)**
- Clone/fork approach
- Pull request workflow
- Human review op kritieke changes
- Compliance met externe regels

### 5.3 Batch Processing Mode
**Voor bulk operaties**
- Parallel execution (5 concurrent repos)
- Progress tracking per project
- Consolidated reporting
- Resource throttling

**Voorbeeld:** Onderhoud van 32 legacy repositories in 1 weekend

---

## 6. SUCCES METRICS

### 6.1 Per Capability

| Capability | Success Metric | Target |
|------------|---------------|--------|
| **Nieuwe projecten** | Time to first deployment | <2 sprints |
| **Project onderhoud** | Dependencies up-to-date | 100% within 7 days |
| **Externe onderhoud** | Pull request acceptance rate | >90% |
| **Kwaliteitsonderzoek** | Critical findings addressed | 100% |
| **Software migratie** | Data integrity | 100% validation |
| **Feature uitvoering** | Backward compatibility | 100% |
| **Bugfixes** | Within SLA time | 95% |

### 6.2 Overall Platform

**Efficiency:**
- 70% of work automated (local agents)
- 30% human-assisted (cloud agents + review)
- Cost reduction: 42-51% vs manual

**Quality:**
- Estimation accuracy: ±10% of actual
- Test coverage: ≥80% line, ≥70% branch
- Technical Debt Ratio: <10%
- 0 Critical security vulnerabilities

**Velocity:**
- Feature → Production: 2 sprints (12 days)
- Bug P0 fix: <4 hours
- Migration: 4 repos/week (batch mode)

---

## 7. USE CASES

### 7.1 Primary Use Case: HCI EPD Migratie

**Input:**
- 1.38M LOC ASP Classic codebase (externe repository)
- 25+ years old
- Target: .NET Core + Blazor
- Compliance: NEN7510, ISO27001

**MarkdownTaskManager Flow:**

> 📋 **Note:** Dit demonstreert de **External Repo Mode** workflow
> Voor externe codebases wordt ALTIJD eerst een Quality Audit uitgevoerd (Capability #3 regel)

**Phase 1: Quality Audit (VERPLICHT voor externe repos)**

1. **Initial Analysis** (QUALITY_AUDIT - Capability #4)
   - Quinn analyzes codebase
   - Identifies 147 security vulnerabilities
   - Calculates Technical Debt Ratio: 18%
   - Generates baseline metrics
   - Creates prioritized remediation plan

**Phase 2: Pre-Migration Maintenance**

2. **Pre-Migration Cleanup** (MAINTENANCE - Capability #3)
   - Marcus fixes critical security issues
   - Updates dependencies waar mogelijk
   - Refactors worst code smells
   - TDR reduced to 12%

3. **Migration Planning** (MIGRATION)
   - Miguel assesses: MCI=185 (HIGH)
   - Eliza estimates: 21 FP, 15 sprints
   - Strategy: Phased migration (module by module)
   - Rollback plan per module

4. **Epic Breakdown** (NEW_FEATURE approach voor nieuwe modules)
   - Felix creates Epic structure:
     - EPIC-E002: Patient Dossier Core (120 SP)
     - EPIC-MED-001: Medication Management (89 SP)
     - EPIC-RAP-001: Reporting Module (55 SP)
   - Complete Feature → Story → Task breakdown

5. **Execution** (MIGRATION + NEW_FEATURE hybrid)
   - Miguel migrates per module
   - Tessa validates functional equivalence
   - Quinn performs security review per module
   - Diana updates documentation

6. **Validation** (QUALITY_AUDIT + TESTING)
   - 100% data integrity validation
   - Performance benchmarking (≥90% baseline)
   - Full security audit
   - Compliance verification (NEN7510)

7. **Cutover** (MIGRATION Stage 5)
   - Phased rollout per module
   - 48h monitoring per deployment
   - Rollback capability tested
   - Final validation

**Result:**
- 15 sprints (30 weeks)
- €36,000 cost savings (51% reduction)
- 0 critical bugs in production
- Full NEN7510 compliance achieved

---

### 7.2 Secondary Use Case: Portfolio Maintenance

**Input:** 32 legacy repositories (verschillende tech stacks)

**Batch Processing:**
- Weekly: Security scans op alle repos (Marcus)
- Monthly: Dependency updates (Marcus)
- Quarterly: Code quality audit (Quinn)
- Yearly: Architecture review (Miguel)

**Automated:**
- Security patches binnen 24h
- Dependency updates binnen 7 dagen
- PR's naar maintainers met uitleg
- Consolidated security dashboard

---

## 8. NEXT STEPS

### 8.1 Immediate (Week 7-8)
- ✅ Week 6: SuperClaude Integration (COMPLEET)
- 🔄 Week 7: Spec-Kit Integration (voor NEW_FEATURE workflow)
- 🔄 Week 8: Code-Maintenance-Agent (voor MAINTENANCE workflow)

### 8.2 Short-term (Week 9-12)
- Function Point Calculator (Intelligence Layer)
- Story Point Estimator (Intelligence Layer)
- Work Type Router (classificatie engine)
- ML-based estimation refinement

### 8.3 Medium-term (Week 13-24)
- WebSocket real-time dashboard
- Quality Gates automation
- BMAD-Method adoption
- Migration workflow completion

### 8.4 Long-term (Week 25-40)
- Pilot migrations (3 repos)
- Full batch migration (32 repos)
- ML model refinement
- Continuous improvement loops

---

## CONCLUSIE

MarkdownTaskManager is een **universal software development platform** dat:

✅ **7 core capabilities** levert via **8 work type streams**
✅ **8 gespecialiseerde agents** deelt over alle workflows
✅ **Eigen én externe projecten** kan beheren
✅ **Van idee tot productie** volledig kan automatiseren
✅ **Legacy naar modern** kan migreren met validatie
✅ **Kwaliteit en veiligheid** continu kan monitoren

**Unique Value Proposition:**
> "Van legacy maintenance tot greenfield development - één platform, één agent pool, alle software lifecycle capabilities."

---

**Document Owner:** MarkdownTaskManager Team
**Review Cycle:** Maandelijks
**Next Review:** Week 12 (eind Intelligence Layer implementatie)
