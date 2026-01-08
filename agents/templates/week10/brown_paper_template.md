# BMAD Brown-Paper Template

**Version**: 1.0
**Purpose**: Brownfield/Migration project definition through 8 strategic questions
**Target**: BROWN_PAPER workflow - Legacy modernization & migration projects
**Agents**: Miguel (Migration) → Peter (PO) → Felix (Architect) → Diana (Docs)

---

## Overview

This template guides the BMAD (Business Model Analysis & Design) brown-paper session for brownfield/migration projects. The session uses **8 carefully crafted questions** to extract the essential information needed to generate a comprehensive **Migration Specification**.

**Brown-Paper** = Brownfield project (modernizing/migrating existing system)
**Green-Paper** = Greenfield project (starting from scratch) - Different template

---

## Key Differences from Green-Paper

| Aspect | Green-Paper | Brown-Paper |
|--------|-------------|-------------|
| **Questions** | 6 strategic | 8 strategic (+ legacy + migration) |
| **Input** | Idea/concept | Existing system + target state |
| **Analysis** | None | Legacy system analysis required |
| **Agents** | Peter → Felix → Diana | Miguel → Peter → Felix → Diana |
| **Output** | Constitution | Migration Specification |
| **Risk Focus** | Technical | + Data migration, backwards compat |

---

## The 8 Strategic Questions

### Question 1: Legacy System Analysis (REQUIRED)
**Question**: "Describe the current legacy system to be migrated"

**Purpose**: Establish clear understanding of the AS-IS state

**Guidance for User**:
- Describe the current technology stack (languages, frameworks, databases)
- Estimate the size (lines of code, number of modules, pages, tables)
- Identify the age of the system and its maintenance state
- List known technical debt and pain points
- Describe current deployment architecture

**Examples**:
- "ASP.NET Web Forms application (.NET Framework 4.8), ~150,000 LOC, 2,320 ASPX pages, SQL Server database with 180 tables. Built in 2008, last major update 2018. Running on-premise Windows Server 2016. Known issues: no automated tests, security vulnerabilities in authentication, poor mobile support."
- "PHP 5.6 monolith with MySQL, ~80,000 LOC, 45 database tables. Mixed MVC and procedural code. No CI/CD, manual FTP deployments."
- "Java EE 6 application on JBoss, ~200,000 LOC, Oracle database. Heavy use of EJBs and JSF. Performance issues under load."

**Constraints**:
- Type: Multiline text
- Max Length: 1000 characters
- Required: YES
- Validation: Must mention at least technology stack and size estimate

---

### Question 2: Migration Target (REQUIRED)
**Question**: "What is the target state after migration?"

**Purpose**: Define the TO-BE architecture and technology choices

**Guidance for User**:
- Specify the target technology stack
- Describe the target architecture pattern (Clean Architecture, Microservices, etc.)
- Define the target deployment platform (Cloud, On-premise, Hybrid)
- List specific technology choices and why

**Examples**:
- ".NET 8 with ASP.NET Core and Blazor Server. Clean Architecture with CQRS pattern. Azure cloud deployment (West Europe). Target: maintainable, testable, secure codebase with 100% test coverage."
- "Spring Boot 3.x with Angular frontend. Microservices architecture on Kubernetes. AWS deployment with RDS PostgreSQL."
- "Node.js/Express backend with React frontend. Serverless on AWS Lambda. DynamoDB for data storage."

**Constraints**:
- Type: Multiline text
- Max Length: 800 characters
- Required: YES
- Validation: Must mention target stack and architecture

---

### Question 3: Migration Strategy (REQUIRED)
**Question**: "What migration strategy will be used?"

**Purpose**: Define HOW the migration will be executed

**Guidance for User**:
- Choose primary strategy: Strangler Fig, Big Bang, or Parallel Run
- Explain phasing approach (which modules first?)
- Define co-existence period (if any)
- Describe rollback strategy

**Migration Strategies**:
| Strategy | Description | Risk | When to Use |
|----------|-------------|------|-------------|
| **Strangler Fig** | Gradually replace components | Low | Large systems, continuous operation required |
| **Big Bang** | Complete replacement at once | High | Small systems, can afford downtime |
| **Parallel Run** | Run both systems simultaneously | Medium | Critical systems, verification needed |

**Examples**:
- "Strangler Fig pattern with YARP reverse proxy. Phase 1: Authentication (Sprint 1-4), Phase 2: User Management (Sprint 5-8), Phase 3: Core Business Logic (Sprint 9-20). Legacy system remains operational until final cutover. Rollback: revert proxy routing to legacy."
- "Big Bang migration during 48-hour maintenance window. Complete data migration, system swap, smoke testing. Rollback: restore from backup, revert DNS."
- "Parallel run for 4 weeks. Both systems receive same input, outputs compared for parity. Gradual user migration with feature flags."

**Constraints**:
- Type: Multiline text
- Max Length: 800 characters
- Required: YES
- Validation: Must mention one of the three strategies

---

### Question 4: Data Migration Approach (REQUIRED)
**Question**: "How will data be migrated?"

**Purpose**: Define data migration strategy and risks

**Guidance for User**:
- Describe database schema changes (if any)
- Define data transformation requirements
- Specify migration tooling approach
- Address data integrity and validation
- Plan for migration testing

**Examples**:
- "Schema preserved - EF Core will map to existing SQL Server schema. No data transformation needed. Migration validation: row counts, checksum comparisons, business rule validation scripts. Dry-run migrations in staging environment before production."
- "Schema evolution required. New normalized schema design. ETL pipeline with Apache Spark for transformation. Data quality checks at each stage. 3 dry-runs before production migration."
- "Gradual data sync using Change Data Capture (CDC). Real-time replication during parallel run period. Final cutover with brief write-freeze."

**Constraints**:
- Type: Multiline text
- Max Length: 600 characters
- Required: YES
- Validation: Must address data integrity

---

### Question 5: Problem Statement (REQUIRED)
**Question**: "What problems does this migration solve?"

**Purpose**: Establish clear business value and ROI

**Guidance for User**:
- Describe the current pain points being addressed
- Quantify the impact if possible (costs, time, risk)
- Explain why migration is necessary NOW
- List what happens if migration is NOT done

**Examples**:
- "Current system has critical security vulnerabilities (end-of-life .NET Framework). No MFA support violates compliance requirements (NEN 7510). Maintenance costs increasing 20% yearly due to scarce legacy skills. Mobile users (40% of workforce) cannot access system effectively."
- "Performance degradation: page loads >10 seconds. Cannot scale beyond 500 concurrent users. Hosting costs €50k/year for aging hardware. New features take 3x longer to implement than industry average."
- "Vendor lock-in with €200k annual license fees. No API for integration with modern tools. Key developer retiring - knowledge transfer critical."

**Constraints**:
- Type: Multiline text
- Max Length: 500 characters
- Required: YES
- Validation: Must contain at least 50 characters

---

### Question 6: Users & Stakeholders (REQUIRED)
**Question**: "Who are the users and stakeholders affected by this migration?"

**Purpose**: Identify impact scope and change management needs

**Guidance for User**:
- List PRIMARY user groups (daily usage)
- List STAKEHOLDERS (decision makers, budget owners)
- Describe change impact per group
- Identify training/communication needs

**Examples**:
- "Primary Users: 200 healthcare workers (daily EPD access), 15 IT administrators (system management). Stakeholders: CTO (budget approval), Compliance Officer (NEN 7510), Department Heads (operational continuity). Impact: New login flow (MFA), refreshed UI. Training: 2-hour session per user group."
- "Users: 50 internal staff, 500 external customers (portal). Stakeholders: CEO, CFO, Customer Success team. High impact for external users - new interface. Phased rollout with beta group."

**Constraints**:
- Type: Multiline text
- Max Length: 400 characters
- Required: YES
- Validation: Must mention at least one user group and one stakeholder

---

### Question 7: Success Criteria (REQUIRED)
**Question**: "What are the measurable success criteria?"

**Purpose**: Define how migration success will be measured

**Guidance for User**:
- Specify MEASURABLE criteria (numbers!)
- Include functional parity requirements
- Include non-functional requirements (performance, security)
- Define post-migration validation period

**Examples**:
- "1) 100% functional parity with legacy system, 2) Page load time <2 seconds (vs current 8s), 3) 100% test coverage on new code, 4) OWASP A+ security rating, 5) Zero data loss during migration, 6) 99.9% uptime post-migration, 7) NEN 7510 compliance certification within 6 months"
- "1) All 150 use cases working in new system, 2) Performance: 2x throughput improvement, 3) Cost: 40% infrastructure cost reduction, 4) User satisfaction: >4.0 rating (vs current 2.8), 5) Bug rate: <5 P1 bugs in first month"

**Constraints**:
- Type: Multiline text
- Max Length: 500 characters
- Required: YES
- Validation: Must contain at least 3 criteria with numbers/metrics

---

### Question 8: Timeline & Constraints (REQUIRED)
**Question**: "What is the timeline and what are the constraints?"

**Purpose**: Set realistic expectations and identify blockers

**Guidance for User**:
- Provide total timeline estimate
- Identify hard deadlines (compliance, contracts, etc.)
- List team constraints (size, availability, skills)
- Mention budget constraints if relevant
- Identify external dependencies

**Examples**:
- "72 weeks total (Sprint 0-36). Hard deadline: NEN 7510 audit in 18 months. Team: Solo developer for Phase 1 (14 weeks), then 8-10 FTE for Phase 2. Budget: €500k approved. Dependencies: Azure subscription approval, legacy database access, stakeholder availability for UAT."
- "6 months to MVP, 12 months to full migration. Deadline: Current hosting contract ends in 14 months. Team: 4 developers, 1 QA, 1 DevOps. External dependency: Third-party API vendor migration timeline."

**Constraints**:
- Type: Multiline text
- Max Length: 400 characters
- Required: YES
- Validation: Must mention timeline and at least one constraint

---

## Miguel's Migration Analysis Prompt

**Context**: Miguel receives Q1-Q4 (legacy, target, strategy, data) and performs initial analysis.

### Prompt Template for Miguel

```markdown
You are Miguel, the Migration Architect agent.

You have received the first 4 questions from a BMAD Brown-Paper session.
Your task is to analyze the migration complexity and identify risks.

## Input: Migration Context

**Q1 - Legacy System**: {{answer_1}}
**Q2 - Migration Target**: {{answer_2}}
**Q3 - Migration Strategy**: {{answer_3}}
**Q4 - Data Migration**: {{answer_4}}

## Your Task

Generate a MIGRATION ANALYSIS with the following structure:

### 1. Complexity Assessment (100-150 words)
- Rate complexity: LOW / MEDIUM / HIGH / VERY HIGH
- Justify the rating based on:
  * Technology gap (legacy vs target)
  * System size and age
  * Data migration complexity
  * Integration dependencies

### 2. Risk Register (200-300 words)
Identify 5-10 key risks:
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | Low/Med/High | Low/Med/High/Critical | Strategy |

### 3. Migration Phases Recommendation (150-200 words)
- Recommend phasing based on:
  * Module dependencies
  * Risk reduction (critical first vs easy wins first)
  * Business value delivery
- Suggest wave structure

### 4. Technical Spikes Required (100-150 words)
List proof-of-concept work needed before full migration:
- Database mapping validation
- Authentication migration
- Performance benchmarking
- Integration testing

### 5. Go/No-Go Checkpoints (50-100 words)
Define decision points where migration should be validated:
- After Phase 1
- Before production cutover
- Post-migration validation period

## Output Format
Return structured JSON matching MigrationAnalysis schema.
```

---

## Peter's Specification Generation Prompt

**Context**: Peter receives all 8 answers + Miguel's analysis to generate the Migration Specification.

### Prompt Template for Peter

```markdown
You are Peter, the Product Owner agent.

You have received a completed BMAD Brown-Paper session for a migration project,
plus Miguel's migration analysis.

## Input: BMAD Answers

**Q1 - Legacy System**: {{answer_1}}
**Q2 - Migration Target**: {{answer_2}}
**Q3 - Migration Strategy**: {{answer_3}}
**Q4 - Data Migration**: {{answer_4}}
**Q5 - Problem Statement**: {{answer_5}}
**Q6 - Users & Stakeholders**: {{answer_6}}
**Q7 - Success Criteria**: {{answer_7}}
**Q8 - Timeline & Constraints**: {{answer_8}}

**Miguel's Analysis**: {{migration_analysis}}

## Your Task

Generate a MIGRATION SPECIFICATION with the following structure:

### 1. Executive Summary (150-200 words)
- Project name and scope
- Migration strategy summary
- Key dates and milestones
- Success criteria summary

### 2. Current State (AS-IS) (200-300 words)
- Technology stack details
- System architecture diagram description
- Known issues and technical debt
- Current metrics (performance, costs, etc.)

### 3. Target State (TO-BE) (200-300 words)
- Target technology stack
- Target architecture pattern
- Deployment architecture
- Expected improvements

### 4. Migration Approach (300-400 words)
- Chosen strategy (Strangler Fig/Big Bang/Parallel)
- Phase breakdown with modules
- Co-existence plan
- Rollback procedures
- Data migration approach

### 5. Stakeholder Analysis (150-200 words)
- User groups with impact assessment
- Stakeholders with responsibilities
- Communication plan
- Training requirements

### 6. Success Criteria (150-200 words)
- Functional parity checklist
- Non-functional requirements
- Validation approach
- Post-migration monitoring

### 7. Timeline & Milestones (200-250 words)
- Phase timeline (weeks)
- Key milestones with deliverables
- Go/No-Go decision points
- Resource allocation per phase

### 8. Risks & Mitigations (150-200 words)
- Top 5 risks from Miguel's analysis
- Mitigation strategies
- Contingency plans

### 9. Assumptions & Dependencies (100-150 words)
- Key assumptions
- External dependencies
- Prerequisites

## Output Requirements

- Total word count: 1500-2000 words
- Format: Structured JSON matching MigrationSpecification schema
- Tone: Professional, clear, actionable
- Include: Mermaid diagrams for timeline and architecture where helpful

Generate the MIGRATION SPECIFICATION now.
```

---

## Felix's Task Generation Prompt

**Context**: Felix receives the Migration Specification and generates Epic/Feature/Story hierarchy.

### Prompt Template for Felix

```markdown
You are Felix, the Feature Architect agent.

You have received a Migration Specification for a brownfield project.
Your task is to generate a complete task hierarchy.

## Input: Migration Specification

{{migration_specification}}

## Your Task

Generate a TASK HIERARCHY with the following structure:

### For Each Migration Phase:

#### Epic
- ID: EPIC-{phase}-{number}
- Title: Clear, action-oriented
- Description: What this epic achieves
- Acceptance Criteria: 3-5 measurable criteria
- Estimated FP: Function Points
- Dependencies: Other epics this depends on

#### Features (3-7 per Epic)
- ID: FEAT-{epic}-{number}
- Title: Specific capability
- Description: What this feature delivers
- Acceptance Criteria: 2-4 criteria
- Estimated SP: Story Points (1-13 scale)
- Parent Epic: Reference

#### Stories (2-5 per Feature)
- ID: STORY-{feature}-{number}
- Title: User story format ("As a... I want... So that...")
- Description: Implementation details
- Acceptance Criteria: Testable criteria
- Estimated SP: Story Points (1-8 scale)
- Definition of Done: Specific for this story
- Parent Feature: Reference

### Task Generation Rules

1. **Phase 1 (Foundation)** should include:
   - Project setup epic
   - Architecture foundation epic
   - Security/Authentication epic

2. **Each subsequent phase** should include:
   - Module migration epic(s)
   - Testing epic
   - Documentation epic

3. **Final Phase** should include:
   - Integration epic
   - Data migration epic
   - Cutover epic
   - Validation epic

### Output Format

Return structured JSON with:
- epics: []
- features: []
- stories: []
- dependencies: {}
- summary: { total_epics, total_features, total_stories, total_fp, total_sp }

Generate the TASK HIERARCHY now.
```

---

## Migration Specification Schema

```json
{
  "specification_id": "uuid",
  "project_id": "uuid",
  "version": 1,
  "status": "draft",
  "type": "BROWN_PAPER",
  "content": {
    "executive_summary": "...",
    "current_state": {
      "technology_stack": [],
      "architecture": "...",
      "known_issues": [],
      "metrics": {}
    },
    "target_state": {
      "technology_stack": [],
      "architecture_pattern": "...",
      "deployment": "...",
      "expected_improvements": []
    },
    "migration_approach": {
      "strategy": "strangler_fig | big_bang | parallel_run",
      "phases": [],
      "coexistence_plan": "...",
      "rollback_procedure": "...",
      "data_migration": {}
    },
    "stakeholders": [],
    "success_criteria": [],
    "timeline": {
      "total_duration_weeks": 72,
      "phases": [],
      "milestones": [],
      "go_no_go_points": []
    },
    "risks": [],
    "assumptions": [],
    "dependencies": []
  },
  "migration_analysis": {
    "complexity": "HIGH",
    "risk_register": [],
    "recommended_phases": [],
    "technical_spikes": [],
    "checkpoints": []
  },
  "metadata": {
    "generated_by": "Peter",
    "analyzed_by": "Miguel",
    "workflow": "BROWN_PAPER",
    "generated_at": "2025-12-08T10:00:00Z",
    "word_count": 1750,
    "bmad_session_id": "uuid"
  }
}
```

---

## Workflow Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BROWN_PAPER WORKFLOW                                  │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │   STAGE 1    │    │   STAGE 2    │    │   STAGE 3    │    │  STAGE 4   ││
│  │   ANALYZE    │───▶│   SPECIFY    │───▶│   GENERATE   │───▶│  REVIEW    ││
│  │   (Miguel)   │    │   (Peter)    │    │   (Felix)    │    │  (Quinn)   ││
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘│
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │ Migration    │    │ Migration    │    │ Task         │    │ Quality    ││
│  │ Analysis     │    │ Spec         │    │ Hierarchy    │    │ Review     ││
│  │ + Risks      │    │ Document     │    │ Epics/       │    │ + Approval ││
│  │              │    │              │    │ Features/    │    │            ││
│  │              │    │              │    │ Stories      │    │            ││
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘│
│                                                                              │
│  Finally: Diana generates documentation                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

```
POST /api/workflows/brown-paper/start
  - Starts BMAD session, returns session_id

POST /api/workflows/brown-paper/{session_id}/answer
  - Submit answer to current question
  - Returns next question or completion status

GET /api/workflows/brown-paper/{session_id}/status
  - Get session status and progress

POST /api/workflows/brown-paper/{session_id}/analyze
  - Trigger Miguel's analysis (after Q1-Q4)

POST /api/workflows/brown-paper/{session_id}/generate
  - Generate full specification (after all questions)

GET /api/workflows/brown-paper/{session_id}/specification
  - Get generated Migration Specification

GET /api/workflows/brown-paper/{session_id}/tasks
  - Get generated Task Hierarchy

POST /api/workflows/brown-paper/{session_id}/review
  - Submit review feedback (approve/reject with comments)
```

---

## Best Practices

### For Users Answering Questions
1. **Be specific about legacy**: Include version numbers, sizes, dates
2. **Quantify problems**: "8 second load time" > "slow"
3. **Think phasing**: What can be migrated independently?
4. **Consider data**: Data migration is often the hardest part
5. **Be realistic**: Migration always takes longer than expected

### For Miguel Analyzing Migration
1. **Validate strategy fit**: Is Strangler Fig really possible?
2. **Identify hidden complexity**: Legacy integrations, undocumented features
3. **Challenge assumptions**: "No schema changes" - is that realistic?
4. **Front-load risks**: Better to know now than during cutover

### For Peter Generating Specs
1. **Stay faithful to answers**: Don't invent requirements
2. **Integrate Miguel's analysis**: Risks should be visible
3. **Clear phases**: Each phase should be independently valuable
4. **Measurable criteria**: Every success criterion needs a number

### For Felix Generating Tasks
1. **Foundation first**: Setup, architecture, auth before features
2. **Vertical slices**: Each feature should be end-to-end testable
3. **Test stories**: Every feature needs corresponding test stories
4. **Migration stories**: Include data migration in relevant phases

---

**Version**: 1.0
**Created**: 2025-12-08
**Status**: Ready for implementation
**Next Review**: After first pilot (HCI-CRS)
