# BMAD Integration Guide
**Business Model Architecture & Design - Integration with Markdown Task Manager**

**Status**: Week 9 Implementation
**Last Updated**: 2025-11-18
**Version**: 1.0

---

## 📋 Executive Summary

BMAD (Business Model Architecture & Design) methodology has been integrated into the Markdown Task Manager to provide structured project definition for both greenfield and brownfield projects. This guide documents the integration architecture, workflows, and usage patterns.

**Key Integration Points**:
1. BMAD Green-Paper Sessions → NEW_FEATURE workflow
2. BMAD Brown-Paper Sessions → Brownfield migration workflow
3. BMAD outputs → Spec-Kit Constitution phase
4. Quality Scans → Brown-Paper pre-population
5. All BMAD documents → ChromaDB RAG storage

---

## 🎯 BMAD Methodology Overview

### What is BMAD?

BMAD is a structured methodology for project definition through facilitated sessions that gather:
- Business vision and goals
- Stakeholder alignment
- Technical constraints
- Risk assessment
- Migration strategies (for brownfield)

### Two Session Types

#### 1. Green-Paper Session (Greenfield Projects)
**Purpose**: Define vision and scope for new development

**Duration**: 2-4 hours
**Participants**: Product Owner, Architect, Key Stakeholders
**Output**: Green-paper document with vision, principles, scope, constraints, risks

**When to Use**:
- Starting a completely new project
- No existing codebase
- Need to align on vision and principles

#### 2. Brown-Paper Session (Brownfield Projects)
**Purpose**: Assess existing code and plan migration/modernization

**Duration**: 3-6 hours
**Participants**: Product Owner, Architect, Developers, QA
**Prerequisites**: Quality scan MUST be run first
**Output**: Brown-paper document with current state, technical debt, migration plan, risks

**When to Use**:
- Migrating legacy system
- Modernizing existing codebase
- Need technical debt assessment
- Planning technology upgrade

---

## 🏗️ Integration Architecture

### System Flow

```
User Creates Project
    ↓
  [Project Type Selection]
    ↓
┌───────────┴──────────┐
│                      │
Greenfield          Brownfield
    ↓                  ↓
Green-Paper      Quality Scan (5-15 min)
Session              ↓
    ↓           Brown-Paper Session
    │                ↓
    └────────┬───────┘
             ↓
    BMAD Output (markdown)
             ↓
    Store in ChromaDB
             ↓
    Spec-Kit Workflow
             ↓
    Constitution → Specification → Tasks
             ↓
    All docs in ChromaDB
             ↓
    Project Status: 'active'
             ↓
    User can start workflows
    (BUG, FEATURE, MAINTENANCE, etc.)
```

### Component Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend UI                         │
│  - Project Selection Screen                     │
│  - BMAD Session Interface                       │
│  - Quality Scan Dashboard                       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│         FastAPI Backend                          │
│  POST /api/projects/new                         │
│  POST /api/projects/{id}/green-paper            │
│  POST /api/projects/{id}/brown-paper            │
│  POST /api/projects/{id}/quality-scan           │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───┴───┐   ┌────┴────┐   ┌───┴────┐
│ PG DB │   │ TypeScript│ │ChromaDB│
│       │   │  Agents   │ │  RAG   │
│Project│   │┌─────────┐│ │  - Documents
│Metadata│  ││Green-   ││ │  - Scans
│       │   ││Paper    ││ │  - Sessions
│bmad_  │   ││Workflow ││ │  - Historical
│session│   │└─────────┘│ │         │
│_id    │   ││Brown-   ││ └─────────┘
│       │   ││Paper    ││
│quality│   ││Workflow ││
│_scan_ │   │└─────────┘│
│id     │   ││Spec-Kit ││
└───────┘   ││Workflow ││
            │└─────────┘│
            └───────────┘
```

---

## 📝 BMAD Templates

### Green-Paper Template

**Location**: `backend/agents/templates/bmadGreenPaperTemplate.ts`

**6 Key Questions**:
1. **Business Vision**: What problem are we solving?
2. **Stakeholders**: Who cares about this project?
3. **Guiding Principles**: What drives our decisions?
4. **Scope**: What's in and out?
5. **Constraints**: Budget, timeline, technology limits?
6. **Known Risks**: What could go wrong?

**Output Structure**:
```typescript
interface GreenPaperOutput {
  vision: { businessGoals, problemStatement, successCriteria }
  stakeholders: { internal, external, decisionMakers }
  principles: { principle, rationale }[]
  scope: { included, excluded, assumptions }
  constraints: { budget, timeline, technology, resources, regulatory }
  risks: { risk, category, impact, probability, mitigation }[]
}
```

### Brown-Paper Template

**Location**: `backend/agents/templates/bmadBrownPaperTemplate.ts`

**7 Key Questions** (with scan data pre-populated):
1. **Current Architecture**: Confirm/correct scan findings
2. **Technical Debt**: Categorize and prioritize debt
3. **Security Vulnerabilities**: OWASP Top 10 remediation
4. **Preservation Needs**: What MUST stay the same?
5. **Improvement Opportunities**: What should we fix?
6. **Migration Strategy**: Big-bang vs. incremental?
7. **Migration Risks**: What are migration-specific risks?

**Output Structure**:
```typescript
interface BrownPaperOutput {
  currentState: { architecture, techStack, linesOfCode, teamFamiliarity }
  technicalDebt: { totalDays, categories, topIssues }
  securityIssues: { critical, high, medium, low, topVulnerabilities }
  preservationNeeds: { feature, reason, complexity }[]
  improvementAreas: { area, currentState, desiredState, priority }[]
  migrationStrategy: { approach, rationale, phases }
  risks: { risk, category, impact, probability, mitigation }[]
}
```

---

## 🔄 BMAD → Spec-Kit Mapping

### Green-Paper → Constitution

```
BMAD Green-Paper              Spec-Kit Constitution
─────────────────             ──────────────────────
Vision Statement       →      Principles (Business Vision)
Business Goals         →      Business Case
Success Criteria       →      Success Metrics

Stakeholders          →      Stakeholders Section
- Internal            →        Internal list
- External            →        External list
- Decision Makers     →        Approval chain

Guiding Principles    →      Core Principles
- Principle           →        Principle name
- Rationale           →        Principle description

Scope                 →      Scope Section
- Included            →        In Scope list
- Excluded            →        Out of Scope list
- Assumptions         →        Assumptions list

Constraints           →      Constraints Section
- Budget              →        Budget constraint
- Timeline            →        Timeline constraint
- Technology          →        Technical constraints
- Resources           →        Resource constraints
- Regulatory          →        Compliance requirements

Risks                 →      Risks Section
- Risk                →        Risk description
- Category            →        Risk type
- Impact/Probability  →        Risk score
- Mitigation          →        Mitigation strategy
```

### Brown-Paper → Constitution

```
BMAD Brown-Paper              Spec-Kit Constitution
────────────────             ──────────────────────
Current State         →      Technical Context
- Architecture        →        Current architecture
- Tech Stack          →        Existing technology
- Team Familiarity    →        Knowledge constraints

Technical Debt        →      Constraints
- Total Days          →        Technical debt estimate
- Categories          →        Debt breakdown
- Top Issues          →        Must-fix items

Security Issues       →      Risks + Requirements
- Vulnerabilities     →        Security risks
- Top Issues          →        Security requirements
- Remediation Plan    →        Mitigation strategy

Preservation Needs    →      Functional Requirements
- Features            →        Must-preserve features
- Reason              →        Business justification

Improvement Areas     →      Quality Requirements
- Current/Desired     →        Performance targets
- Priority            →        Requirement priority

Migration Strategy    →      Constraints + Approach
- Approach            →        Migration methodology
- Phases              →        Implementation phases
- Deliverables        →        Phase outcomes

Risks                 →      Risks Section
- Migration-specific  →        Risk descriptions
- Impact/Probability  →        Risk scores
- Mitigation          →        Mitigation plans
```

---

## 💾 ChromaDB Storage Strategy

### Collections Used

1. **bmad_sessions** collection
   - Stores complete green-paper and brown-paper markdown
   - Metadata: project_id, session_type, participants
   - Enables semantic search of past sessions

2. **project_documents** collection
   - Stores constitution, specification, tasks
   - Links to original BMAD session via metadata
   - Chunked for efficient retrieval

3. **code_analysis** collection
   - Stores quality scan results (for brownfield)
   - Pre-scan data used in brown-paper
   - Historical technical debt tracking

4. **historical_projects** collection
   - Full project metadata post-completion
   - Used for similarity search
   - Estimation improvement via ML

### Storage Workflow

```python
# Green-Paper Session
1. User completes green-paper questions
2. Generate green-paper markdown
3. ChromaService.store_bmad_session(
     project_id,
     'green-paper',
     session_data,
     markdown_content
   )
4. Return session_id for database reference

# Brown-Paper Session (with scan)
1. Run quality scan first
2. ChromaService.store_quality_scan(project_id, scan_results)
3. Pre-populate brown-paper form with scan data
4. User completes brown-paper questions
5. Generate brown-paper markdown (includes scan summary)
6. ChromaService.store_bmad_session(
     project_id,
     'brown-paper',
     session_data,
     markdown_content
   )
7. Return session_id for database reference

# Spec-Kit Integration
1. Retrieve BMAD session: ChromaService.get_bmad_session(session_id)
2. Map BMAD output → Constitution input
3. Run Spec-Kit workflow (constitution → spec → tasks)
4. Store all generated docs:
   ChromaService.store_document(project_id, 'constitution', content)
   ChromaService.store_document(project_id, 'specification', content)
   ChromaService.store_document(project_id, 'tasks', content)
```

---

## 🔍 Quality Scan Integration (Brownfield)

### Scan Execution Flow

```
User Creates Brownfield Project
    ↓
Quality Scan Triggered Automatically
    ↓
Scan Components (5-15 minutes):
  1. Code Metrics (LOC, complexity)
  2. Architecture Analysis (/architect command)
  3. Security Scan (/security OWASP Top 10)
  4. Quality Gates (42 validation rules)
  5. Test Coverage Analysis
  6. Dependency Audit
  7. Technical Debt Estimation
    ↓
Scan Results Stored in ChromaDB
    ↓
Scan Summary Displayed to User
    ↓
Brown-Paper Session Started
    ↓
Form Pre-Populated with Scan Data
```

### Scan Result Structure

```typescript
interface QualityScanResult {
  scan_id: string;
  project_id: number;
  overall_score: number;  // 0-100%
  security_score: number;
  quality_score: number;
  test_coverage: number;
  tech_debt_days: number;
  total_violations: number;
  architecture_pattern: string;
  tech_stack: string[];
  lines_of_code: number;
  violations: {
    gate_type: string;  // Architecture, Security, Quality, etc.
    rule: string;
    severity: "low" | "medium" | "high" | "critical";
    count: number;
    description: string;
    recommendation: string;
  }[];
  scanned_at: string;
}
```

---

## 🚀 Usage Examples

### Example 1: Greenfield Project

```typescript
// 1. User creates new project
POST /api/projects/new
{
  "type": "greenfield",
  "name": "Patient Portal v2.0",
  "description": "Modern patient engagement platform"
}

// 2. Start green-paper session
POST /api/projects/123/green-paper
{
  "facilitator": "John Doe",
  "participants": ["Jane Smith", "Bob Johnson"]
}

// 3. User answers 6 questions via UI

// 4. System generates green-paper.md and stores in ChromaDB
{
  "session_id": "green-paper-123-2025-11-18",
  "workflow_status": "started",
  "next_step": "spec-kit-constitution"
}

// 5. Spec-Kit workflow runs automatically
//    Constitution → Specification → Tasks

// 6. Project status → 'active'
// 7. User can now select workflows (BUG, FEATURE, etc.)
```

### Example 2: Brownfield Project

```typescript
// 1. User creates brownfield project + uploads code
POST /api/projects/new
{
  "type": "brownfield",
  "name": "HCI EPD Migration",
  "description": "Migrate legacy ASP.NET to .NET Core",
  "codebase_path": "/path/to/code"
}

// 2. Quality scan runs automatically (5-15 min)
POST /api/projects/456/quality-scan (automatic)

// Scan result:
{
  "scan_id": "scan-456-2025-11-18",
  "overall_score": 65,
  "security_score": 58,
  "tech_debt_days": 180,
  "total_violations": 287,
  "top_violations": [
    {
      "type": "SQL Injection",
      "severity": "critical",
      "count": 12,
      "description": "User input not sanitized"
    },
    ...
  ]
}

// 3. User reviews scan results, then starts brown-paper
POST /api/projects/456/brown-paper
{
  "facilitator": "Jane Doe",
  "participants": ["John Smith", "Alice Brown"],
  "scan_id": "scan-456-2025-11-18"
}

// 4. Brown-paper form PRE-POPULATED with scan data
// 5. User confirms/corrects and answers additional questions

// 6. System generates brown-paper.md with scan summary
{
  "session_id": "brown-paper-456-2025-11-18",
  "scan_id": "scan-456-2025-11-18",
  "workflow_status": "started",
  "next_step": "spec-kit-constitution"
}

// 7. Spec-Kit workflow runs (with migration context)
// 8. Project status → 'active'
```

---

## ✅ Success Criteria

### Week 9 Complete:
- ✅ BMAD framework directory created
- ✅ Green-paper template implemented (300+ lines)
- ✅ Brown-paper template implemented (350+ lines)
- ✅ BMAD → Spec-Kit mapping documented
- ✅ ChromaDB integration strategy defined
- ✅ Quality scan integration planned

### Week 10 (GREEN_PAPER_PROJECT):
- [ ] GREEN_PAPER_PROJECT workflow implementation
- [ ] BMAD facilitator interactive UI
- [ ] Automatic Spec-Kit triggering
- [ ] ChromaDB storage working
- [ ] End-to-end greenfield flow

### Week 11 (BROWN_PAPER_PROJECT):
- [ ] Quality scan automation
- [ ] BROWN_PAPER_PROJECT workflow
- [ ] Scan result pre-population
- [ ] RAG similarity search for brownfield projects
- [ ] End-to-end brownfield flow

---

## 📚 References

### BMAD Framework
- **Location**: `/external-frameworks/bmad-method/`
- **Status**: Placeholder (repositories to be cloned)
- **Repos**: bmad-method, bmad-expanded

### Templates
- Green-Paper: `backend/agents/templates/bmadGreenPaperTemplate.ts`
- Brown-Paper: `backend/agents/templates/bmadBrownPaperTemplate.ts`

### Services
- ChromaDB: `backend/app/services/chroma_service.py`
- Embedding: `backend/app/services/embedding_service.py`

### Workflows (To Be Implemented)
- Week 10: `backend/agents/workflows/greenPaperWorkflow.ts`
- Week 11: `backend/agents/workflows/brownPaperWorkflow.ts`

### Related Documentation
- **PROJECT_STATUS_SUMMARY.md**: Overall project status
- **ROADMAP.md**: 40-week planning (Week 9-21 BMAD integration)
- **AGENTS.md**: Agent system reference
- **ARCHITECTURE.md**: Technical architecture

---

**Version**: 1.0
**Status**: Week 9 Foundation Complete ✅
**Next**: Week 10 GREEN_PAPER_PROJECT Workflow Implementation
