# HCI EPD Project - Complete Roadmap & Board Structure Plan

**Project:** HCI EPD Migratie (ASP Classic/ASP.NET → .NET Core/Blazor)  
**Codebase:** 1.38M LOC, 25+ years old  
**Goal:** Modernization with compliance (NEN7510, ISO27001)  
**PM/SM:** Eddie (ROSK Consulting)  
**Date:** November 2025

---

## TABLE OF CONTENTS

1. [Overview & Structure](#1-overview-structure)
2. [Epic Definitions](#2-epic-definitions)
3. [Complete HCI EPD Epics](#3-complete-hci-epd-epics)
4. [Feature Structure](#4-feature-structure)
5. [User Story Structure](#5-user-story-structure)
6. [Sprint Structure](#6-sprint-structure)
7. [Board Views](#7-board-views)
8. [Metadata & Tags](#8-metadata-tags)
9. [Dependencies](#9-dependencies)
10. [Risk Tracking](#10-risk-tracking)
11. [Definition of Done](#11-definition-of-done)
12. [Reporting & Metrics](#12-reporting-metrics)
13. [MD File Implementation](#13-md-file-implementation)
14. [Automation & Tooling](#14-automation-tooling)
15. [Implementation Roadmap](#15-implementation-roadmap)
16. [Recommendations](#16-recommendations)
17. [Appendix](#17-appendix)

---

## 1. OVERVIEW & STRUCTURE

### 1.1 Hierarchy Levels

```
PROJECT: HCI EPD Modernisatie
│
├── FASE: Initiatie / Realisatie / Implementatie
│   │
│   └── EPIC: Module or Technical Component (Board View - 50-150 SP)
│       │
│       └── FEATURE: Functional Building Block (15-40 SP, 2-4 sprints)
│           │
│           └── USER STORY: Team Backlog Item (1-13 SP, 1 sprint)
│               │
│               └── TASK: Technical Work (hours, not points)
```

### 1.2 Views per Stakeholder

| Stakeholder | View Level | Frequency | Purpose |
|-------------|-----------|-----------|---------|
| **Board** | Epic | Monthly | Strategic progress, ROI, risks |
| **Product Owner** | Feature | Weekly | Backlog prioritization |
| **Dev Team** | Story/Task | Daily | Sprint execution |
| **PM/SM (Eddie)** | All levels | Continuous | Translation between views |

### 1.3 Why This Structure?

**The Missing Layer Problem:**
- Board doesn't care about individual stories (too granular)
- Team can't plan around vague epics (too abstract)
- **Solution:** EPIC layer bridges this gap

**Epic = Board's Unit of Measurement:**
- Functional Epics: "Module Patiëntendossier is live"
- Technical Epics: "15 libraries migrated, enables new features"
- Compliance Epics: "NEN7510 compliant, audit-ready"

---

## 2. EPIC DEFINITIONS

### 2.1 Epic Types

**Type 1: FUNCTIONAL (Visible Business Value)**
- Direct user-facing features
- Example: "Electronic Patient Dossier Module"
- Board sees: New functionality deployed

**Type 2: TECHNICAL (Essential Infrastructure)**
- Not user-visible but necessary
- Example: "ASP Classic → .NET Core Migration"
- Board sees: Foundation for future work + cost justification
- **CRITICAL:** Always include business justification

**Type 3: COMPLIANCE/SECURITY (Regulatory)**
- Required for GO-live
- Example: "NEN7510 Audit Trail Implementation"
- Board sees: Legal compliance achieved

### 2.2 Epic Attributes (YAML Frontmatter)

```yaml
epic_id: EPD-E002
epic_name: "Electronic Patient Dossier - Core"
epic_type: FUNCTIONAL | TECHNICAL | COMPLIANCE
fase: INITIATIE | REALISATIE | IMPLEMENTATIE
business_value: "Doctors can digitally view/edit patient data"
board_visibility: YES | NO
priority: CRITICAL | HIGH | MEDIUM | LOW
story_points_total: 120
story_points_completed: 45
completion_percentage: 38%
start_date: 2025-11-01
target_completion: 2026-02-15
status: NOT_STARTED | IN_PROGRESS | BLOCKED | COMPLETED
owner: "Eddie"
dependencies: [EPD-E005, EPD-E012]
risks: ["Telerik license blocking", "Legacy DB complexity"]
```

### 2.3 Epic Naming Conventions

**Functional Epics:**
- `EPD-E0xx`: Core EPD functionality
- `MED-E0xx`: Medication management
- `RAP-E0xx`: Reporting & Analytics
- `ADM-E0xx`: Administration

**Technical Epics:**
- `MIG-E0xx`: Migration (ASP → .NET)
- `LIB-E0xx`: Library & Framework updates
- `INF-E0xx`: Infrastructure & DevOps
- `PER-E0xx`: Performance optimization

**Compliance Epics:**
- `SEC-E0xx`: Security hardening
- `COM-E0xx`: Compliance (NEN7510, ISO27001)
- `AUD-E0xx`: Audit & Logging

---

## 3. COMPLETE HCI EPD EPICS

### FASE 1: INITIATIE (Q4 2025)

#### EPD-E001: Assessment & Architecture
- **Type:** TECHNICAL
- **Business Value:** Foundation for migration, risk identification
- **SP Total:** 34
- **Target:** 2025-12-15
- **Features:**
  - Codebase quality analysis
  - Target architecture design
  - Migration strategy
  - Risk assessment

#### MIG-E001: Proof of Concept
- **Type:** TECHNICAL
- **Business Value:** Validate feasibility, realistic effort estimates
- **SP Total:** 21
- **Target:** 2025-12-20
- **Features:**
  - Migrate 1 representative module
  - Test auth & session management
  - Performance benchmark

---

### FASE 2: REALISATIE (Q1-Q3 2026)

#### EPD-E002: Patient Dossier Core ⭐ CRITICAL
- **Type:** FUNCTIONAL
- **Business Value:** Doctors can view/edit digital patient records
- **SP Total:** 120
- **Target:** Q1 2026
- **Dependencies:** MIG-E002, SEC-E001
- **Features:**
  1. Patient search & selection (21 SP)
  2. Dossier viewing (34 SP)
  3. Dossier editing (28 SP)
  4. Document management (21 SP)
  5. Access control (16 SP)
- **Risks:** Legacy DB schema complexity

#### MED-E001: Medication Management
- **Type:** FUNCTIONAL
- **Business Value:** Safe medication prescribing with interaction checks
- **SP Total:** 89
- **Target:** Q2 2026
- **Dependencies:** EPD-E002, COM-E001
- **Features:**
  - Medication prescribing
  - Interaction checking (G-standard)
  - Medication overview
  - E-prescribing
- **Risks:** G-standard API integration

#### RAP-E001: Reporting Module
- **Type:** FUNCTIONAL
- **Business Value:** Management insights into care delivery
- **SP Total:** 55
- **Target:** Q3 2026
- **Dependencies:** EPD-E002, MED-E001
- **Features:**
  - Standard reports (DBC, production)
  - Custom query builder
  - Export (Excel/PDF)
  - Management dashboard

#### MIG-E002: Core Libraries Migration ⭐ CRITICAL
- **Type:** TECHNICAL
- **Business Value:** Technical foundation for all new features
- **SP Total:** 144
- **Target:** Q1 2026
- **Board Justification:**
  > Current libraries are end-of-life and block new features.
  > Without this migration we cannot:
  > - Implement modern authentication (SSO)
  > - Deploy to cloud
  > - Apply security patches
- **Features:**
  - Authentication library (25k LOC)
  - Database access layer (40k LOC)
  - Business logic layer (60k LOC)
  - Reporting engine (19k LOC)
- **Technical Debt:**
  - MyGeneration deprecated since 2010
  - Telerik components end-of-life
  - SQL injection vulnerabilities

#### LIB-E001: Telerik Component Upgrade
- **Type:** TECHNICAL
- **Business Value:** UI remains functional, license compliance
- **SP Total:** 34
- **Target:** Q1 2026
- **Status:** 🔴 BLOCKED (waiting for license approval)
- **Board Justification:**
  > Current Telerik version end-of-support.
  > Without upgrade: security risks + no vendor support.

#### INF-E001: CI/CD Pipeline
- **Type:** TECHNICAL
- **Business Value:** Faster releases, fewer bugs, higher quality
- **SP Total:** 55
- **Target:** Q1 2026
- **Board Justification:**
  > Manual deployment: 2 days per release
  > Automated: 30 minutes
  > ROI: 16 hours saved per month = €3.2K/month
- **Features:**
  - Azure DevOps pipeline
  - Automated testing (60% coverage target)
  - Integration tests
  - Auto-deployment to test/acceptance

#### PER-E001: Performance Optimization
- **Type:** TECHNICAL
- **Business Value:** 40% faster response times
- **SP Total:** 34
- **Target:** Q2 2026
- **Board Justification:**
  > Current: 3-5 second dossier load time
  > Target: <1 second
  > Impact: 2500 users × 50 dossiers/day = major efficiency gain

#### SEC-E001: Authentication & Authorization ⭐ CRITICAL
- **Type:** COMPLIANCE
- **Business Value:** Secure access, SSO enabled, NEN7510 compliant
- **SP Total:** 55
- **Target:** Q1 2026
- **Compliance:** NEN7510 (access security), ISO27001
- **Features:**
  - OAuth 2.0 / OpenID Connect
  - Role-based access control
  - Multi-factor authentication
  - Session management

#### COM-E001: NEN7510 Logging & Audit ⭐ CRITICAL
- **Type:** COMPLIANCE
- **Business Value:** Required for GO-live, prevents fines (€20M max)
- **SP Total:** 44
- **Target:** Q2 2026
- **Compliance:**
  - NEN7510 Article 8: Logging access to patient data
  - GDPR Article 30: Processing register
  - ISO27001: Audit trails
- **Board Justification:**
  > Legally required for patient data processing.
  > Without this: NO GO-LIVE possible.
  > IGZ audit requirement.
- **Features:**
  - Logging framework (who, what, when)
  - Audit trail viewer
  - Retention policy (7 years)
  - Tamper-proof logging

#### AUD-E001: Security Hardening
- **Type:** COMPLIANCE
- **Business Value:** Vulnerabilities fixed, data breach risk eliminated
- **SP Total:** 89
- **Target:** Q2 2026
- **Board Justification:**
  > Current code has known security issues:
  > - SQL injection: 72 locations
  > - XSS vulnerabilities: 43 locations
  > - Hardcoded credentials: 12 locations
  > Data breach risk: €10M+ fine + reputation damage
- **Features:**
  - SQL injection fixes
  - XSS protection
  - Secrets management (Azure Key Vault)
  - Encryption at rest
  - Penetration testing

---

### FASE 3: IMPLEMENTATIE (Q4 2026)

#### IMP-E001: Pilot Deployment
- **Type:** FUNCTIONAL
- **Business Value:** Production validation with limited scope
- **SP Total:** 55
- **Target:** Q4 2026
- **Features:**
  - Pilot department selection
  - User training & onboarding
  - Hypercare support (4 weeks)
  - Feedback processing

#### IMP-E002: Full Rollout
- **Type:** FUNCTIONAL
- **Business Value:** All users on new platform, legacy decommissioned
- **SP Total:** 89
- **Target:** Q4 2026
- **Dependencies:** IMP-E001
- **Features:**
  - Phased rollout per department
  - Historical data migration
  - User training (all users)
  - Legacy system decommissioning

---

## 4. FEATURE STRUCTURE

### 4.1 Feature Definition

A Feature is a **functional building block** within an Epic that:
- Delivers standalone value (can be tested/demoed independently)
- Completable within 2-4 sprints
- Consists of 3-8 User Stories
- Estimated in Story Points

### 4.2 Feature Attributes

```yaml
feature_id: EPD-F001
feature_name: "Patient Search & Selection"
parent_epic: EPD-E002
business_value: "Doctors can quickly find patients"
acceptance_criteria:
  - "Search by name, BSN, DOB"
  - "Results within 500ms"
  - "Privacy filtering (authorized patients only)"
story_points_total: 21
story_points_completed: 0
status: NOT_STARTED | IN_PROGRESS | TESTING | DONE
priority: HIGH
estimated_sprints: 2
dependencies: [SEC-F001]
```

### 4.3 Example: EPD-E002 Feature Breakdown

**Epic: EPD-E002 - Patient Dossier Core (120 SP)**

```
├── EPD-F001: Patient Search (21 SP)
│   ├── S001: Search by name (5 SP)
│   ├── S002: Search by BSN (3 SP)
│   ├── S003: Recent patients (5 SP)
│   ├── S004: Performance test (3 SP)
│   └── S005: Privacy filtering (5 SP)
│
├── EPD-F002: Dossier Viewing (34 SP)
│   ├── S006: View anamnesis (8 SP)
│   ├── S007: View diagnoses (8 SP)
│   ├── S008: View medication (8 SP)
│   ├── S009: View documents (5 SP)
│   └── S010: Performance test large dossiers (5 SP)
│
├── EPD-F003: Dossier Editing (28 SP)
│   ├── S011: Add anamnesis entry (8 SP)
│   ├── S012: Register diagnosis (8 SP)
│   ├── S013: Correct entry (7 SP)
│   └── S014: Audit logging mutations (5 SP)
│
├── EPD-F004: Document Management (21 SP)
│   ├── S015: Upload PDF (5 SP)
│   ├── S016: Upload photos (5 SP)
│   ├── S017: Link document to dossier (6 SP)
│   └── S018: Virus scanning (5 SP)
│
└── EPD-F005: Access Control (16 SP)
    ├── S019: Role-based access check (8 SP)
    ├── S020: Access review (5 SP)
    └── S021: Integration test with SEC-E001 (3 SP)
```

---

## 5. USER STORY STRUCTURE

### 5.1 Story Template (Connextra Format)

```yaml
story_id: EPD-S001
story_name: "As doctor I want to search patient by name"
parent_feature: EPD-F001
parent_epic: EPD-E002

user_story: |
  As a doctor
  I want to search patients by (part of) their name
  So that I can quickly select the right patient

acceptance_criteria:
  - Given: I'm logged in as doctor
    When: I type min 3 letters of a name
    Then: I see list of all patients whose first/last name matches
  
  - Given: Multiple patients with same name
    When: I see search results
    Then: I also see DOB to distinguish
  
  - Given: I don't have access to a patient
    When: That patient matches my search
    Then: I do NOT see this patient (privacy)
  
  - Given: I have >1000 patients in my care group
    When: I perform a search
    Then: I get results within 500ms

story_points: 5
priority: HIGH
sprint: "Sprint 5"
assigned_to: "Dev A, Dev B"
status: TODO | IN_PROGRESS | IN_REVIEW | TESTING | DONE
tags: [frontend, api, database]

tasks:
  - EPD-T001: Frontend search component (6h)
  - EPD-T002: Backend API endpoint (8h)
  - EPD-T003: Database query + index (4h)
  - EPD-T004: Unit tests (6h)
  - EPD-T005: Integration test (4h)

dependencies:
  - SEC-S001: "Role-based access must be live"

definition_of_done:
  - Code review approved
  - Unit test coverage >80%
  - Integration test passed
  - Performance test <500ms
  - Security review passed
  - Documentation updated
  - Demo to PO approved
```

---

## 6. SPRINT STRUCTURE

### 6.1 Sprint Attributes

```yaml
sprint_id: S005
sprint_name: "Sprint 5 - EPD Search & Auth"
start_date: 2025-11-20
end_date: 2025-12-03
duration_weeks: 2
team_capacity_sp: 45
committed_sp: 42
completed_sp: 0
velocity_previous_3: [38, 41, 39]  # Avg: 39 SP

focus_epics:
  - EPD-E002 (Patient Dossier)
  - SEC-E001 (Authentication)

committed_stories:
  - EPD-S001 (5 SP)
  - EPD-S002 (3 SP)
  - EPD-S003 (5 SP)
  - SEC-S001 (8 SP)
  - SEC-S002 (5 SP)
  - MIG-S001 (13 SP)
  - AUD-S001 (3 SP)

sprint_goal: "Doctors can search patients with modern authentication"

risks:
  - "OAuth integration with legacy AD may be complex"
  - "Auth library migration might take longer (13 SP is high)"
```

### 6.2 Sprint Kanban Columns

**Team Board (Story level):**
```
TODO → IN PROGRESS → IN REVIEW → TESTING → DONE
```

**Task Board (optional, within story):**
```
BACKLOG → TODO → DOING → CODE REVIEW → TESTING → DONE
```

---

## 7. BOARD VIEWS

### 7.1 Board Dashboard (Epic View)

**Purpose:** Strategic overview for stakeholders

**Columns:**
```
PLANNED → IN PROGRESS → TESTING → COMPLETED
```

**Card Format:**
```
┌─────────────────────────────────────────┐
│ EPD-E002: Patient Dossier Core          │
│ Type: FUNCTIONAL | Priority: CRITICAL   │
├─────────────────────────────────────────┤
│ Progress: ████████░░░░░░░░ 45% (54/120)│
│ Status: IN PROGRESS                     │
│ Target: Q1 2026                         │
├─────────────────────────────────────────┤
│ Business Value:                         │
│ "Doctors can digitally manage dossiers" │
├─────────────────────────────────────────┤
│ Current Sprint: S005                    │
│ Features Done: 1/5                      │
│ Risks: 🟡 Legacy DB complexity          │
├─────────────────────────────────────────┤
│ Dependencies:                           │
│ ✓ MIG-E002 (Done)                       │
│ ⏳ SEC-E001 (In progress)               │
└─────────────────────────────────────────┘
```

**Filters:**
- Epic Type: ALL | FUNCTIONAL | TECHNICAL | COMPLIANCE
- Phase: ALL | INITIATIE | REALISATIE | IMPLEMENTATIE
- Status: ALL | NOT_STARTED | IN_PROGRESS | BLOCKED | COMPLETED
- Priority: ALL | CRITICAL | HIGH | MEDIUM | LOW

### 7.2 Product Owner View (Feature View)

**Purpose:** Backlog prioritization and planning

**Columns:**
```
BACKLOG → READY → IN PROGRESS → REVIEW → DONE
```

### 7.3 Development Team View (Story/Task View)

**Purpose:** Daily work, sprint execution

**Sprint Board:**
```
Sprint 5 (42 SP committed)

TODO (20 SP)
├── EPD-S003 (5 SP)
├── SEC-S002 (5 SP)
└── MIG-S001 (13 SP)

IN PROGRESS (12 SP)
├── EPD-S001 (5 SP) - Dev A
└── SEC-S001 (8 SP) - Dev B

IN REVIEW (5 SP)
└── EPD-S002 (3 SP)

TESTING (5 SP)
└── AUD-S001 (3 SP)

DONE (0 SP)
```

---

## 8. METADATA & TAGS

### 8.1 Standard Tags

**Priority:**
- 🔴 CRITICAL - Blocks GO-live
- 🟠 HIGH - Important for roadmap
- 🟡 MEDIUM - Normal priority
- 🟢 LOW - Nice to have

**Status:**
- ⚪ NOT_STARTED
- 🔵 IN_PROGRESS
- 🟣 IN_REVIEW
- 🟡 BLOCKED
- 🟢 COMPLETED

**Type:**
- 📱 FUNCTIONAL
- 🔧 TECHNICAL
- 🔒 COMPLIANCE
- 📊 REPORTING
- 🏗️ INFRASTRUCTURE

### 8.2 Technical Tags

```
#frontend #backend #database #integration
#performance #security #testing
#epd #medicatie #rapportage #administratie
#tech-debt #bug #refactor #documentation
```

---

## 9. DEPENDENCIES

### 9.1 Dependency Types

**BLOCKS:**
```yaml
epic: EPD-E002
blocks:
  - MED-E001  # Medication needs EPD Core
  - RAP-E001  # Reporting needs EPD data
```

**DEPENDS_ON:**
```yaml
epic: EPD-E002
depends_on:
  - MIG-E002  # Needs migrated auth library
  - SEC-E001  # Needs modern authentication
```

### 9.2 Dependency Visualization

```
MIG-E002 ──┬──> EPD-E002 ──┬──> MED-E001
           │               │
SEC-E001 ──┘               └──> RAP-E001
           │
COM-E001 ──┘
```

### 9.3 Critical Path

```
Phase 1: MIG-E001 (PoC) → EPD-E001 (Assessment)
Phase 2: MIG-E002 (Libraries) → SEC-E001 (Auth) → EPD-E002 (Core) → MED-E001
Phase 3: IMP-E001 (Pilot) → IMP-E002 (Rollout)
```

---

## 10. RISK TRACKING

### 10.1 Risk Attributes

```yaml
risk_id: R001
risk_name: "Telerik license approval delayed"
related_epic: LIB-E001
impact: HIGH
probability: MEDIUM
risk_score: 12
status: OPEN | MITIGATED | CLOSED
mitigation_plan: |
  - Parallel: research alternative libraries
  - Escalate to Telerik account manager
  - Backup: build custom components (+34 SP)
owner: "Eddie"
review_date: 2025-11-30
```

### 10.2 Top Risks HCI EPD

1. **R001: Telerik License** (🟠 HIGH × MEDIUM)
2. **R002: Legacy DB Schema** (🔴 CRITICAL × MEDIUM) - MITIGATED
3. **R003: G-standard API** (🟠 HIGH × LOW)
4. **R004: Team Capacity** (🟡 MEDIUM × HIGH) - MITIGATED
5. **R005: NEN7510 Audit** (🔴 CRITICAL × LOW)

---

## 11. DEFINITION OF DONE

### 11.1 DoD per Level

**Epic DoD:**
- All features completed
- Epic acceptance criteria validated
- Demo to stakeholders
- Business value realized
- Documentation updated
- Production deployment
- Hypercare complete (2 weeks)

**Feature DoD:**
- All stories completed
- Feature acceptance criteria validated
- Demo to Product Owner
- Integration tests passed
- Performance tests passed
- Security review passed

**Story DoD:**
- Code complete and pushed
- Code review approved
- Unit test coverage >80%
- All acceptance criteria validated
- Integration test passed
- No critical/high bugs
- Demo to team + PO
- Documentation updated

**Task DoD:**
- Code committed
- Self-review complete
- No linting errors
- Local testing passed

---

## 12. REPORTING & METRICS

### 12.1 Monthly Board Report Template

```markdown
# HCI EPD - Monthly Report [MONTH YEAR]

## Executive Summary
- Status: 🟢 ON TRACK | 🟡 AT RISK | 🔴 DELAYED
- Budget: €XXX / €800K (XX%)
- Timeline: Month X / 12
- Key achievement: [highlight]
- Key risk: [top risk]

## Epic Progress (Functional)

| Epic | Progress | Target | Status | Risks |
|------|----------|--------|--------|-------|
| EPD-E002 | 45% | Q1 2026 | 🟢 | Legacy DB |
| MED-E001 | 25% | Q2 2026 | 🟡 | G-standard |

## Epic Progress (Technical & Compliance)

| Epic | Progress | Target | Status | Justification |
|------|----------|--------|--------|---------------|
| MIG-E002 | 30% | Q1 2026 | 🟢 | Foundation for features |
| SEC-E001 | 20% | Q1 2026 | 🟢 | Required for GO-live |

## Velocity & Capacity
- Avg velocity: 39 SP/sprint
- Completed this month: 78 SP
- Remaining: 1510 SP (~19 sprints)

## Top 3 Risks
1. Telerik License (🟠 HIGH)
2. G-standard Integration (🟡 MEDIUM)
3. Team Capacity Q4 (🟢 LOW)

## Next Month Focus
- Complete EPD-E002 Feature 1 & 2
- Start MED-E001
- Finalize SEC-E001

## Decisions Needed
1. [Decision 1]
2. [Decision 2]
```

### 12.2 Key Metrics

**Velocity:**
- Committed vs Completed SP per sprint
- Average velocity (rolling 3 sprints)
- Velocity trend

**Progress:**
- Epic completion %
- Feature completion %
- Project completion %
- Sprint goal achievement rate

**Quality:**
- Bugs per sprint
- Code coverage %
- Code review cycle time
- Failed builds

**Efficiency:**
- Cycle time (started → done)
- Lead time (created → done)
- WIP limit adherence

---

## 13. MD FILE IMPLEMENTATION

### 13.1 Directory Structure

```
hci-epd-project/
│
├── README.md
├── ROADMAP.md (this file)
│
├── epics/
│   ├── EPD-E001_assessment.md
│   ├── EPD-E002_patientendossier.md
│   ├── MIG-E001_poc.md
│   └── ...
│
├── features/
│   ├── EPD-F001_patient_search.md
│   ├── EPD-F002_dossier_view.md
│   └── ...
│
├── stories/
│   ├── sprint-05/
│   │   ├── EPD-S001_search_by_name.md
│   │   └── ...
│   ├── sprint-06/
│   └── backlog/
│
├── sprints/
│   ├── sprint-01/
│   │   ├── planning.md
│   │   ├── review.md
│   │   └── retrospective.md
│   └── ...
│
├── boards/
│   ├── board-epic-view.md
│   ├── product-backlog.md
│   ├── sprint-board.md
│   └── completed.md
│
├── reports/
│   ├── 2025-11-monthly.md
│   └── metrics-dashboard.md
│
├── risks/
│   └── risk-register.md
│
└── docs/
    ├── definition-of-done.md
    ├── workflow.md
    └── templates/
        ├── epic-template.md
        ├── feature-template.md
        ├── story-template.md
        └── sprint-template.md
```

### 13.2 File Templates

**Epic Template** (`docs/templates/epic-template.md`):
```markdown
---
epic_id: XXX-E000
epic_name: "Epic Name"
epic_type: FUNCTIONAL | TECHNICAL | COMPLIANCE
fase: PHASE
board_visibility: YES | NO
priority: CRITICAL | HIGH | MEDIUM | LOW
status: NOT_STARTED | IN_PROGRESS | BLOCKED | COMPLETED
owner: Eddie
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Epic: [ID] - [Name]

## Metadata
- Type: [Type]
- Phase: [Phase]
- Priority: [Priority]
- Status: [Status]

## Progress
- Story Points: X / Y (Z%)
- Features: X / Y completed
- Target: [Date]

## Business Value
[Description of business value]

## Goals & Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Features
### Completed
- None

### In Progress
- [Feature links]

### Planned
- [Feature links]

## Dependencies
### Blocks
- [Epic links]

### Depends On
- [Epic links]

## Risks & Issues
[List]

## Sprint History
| Sprint | Committed | Completed | Notes |
|--------|-----------|-----------|-------|

## Timeline
[Visual timeline]

## Notes
[Additional notes]
```

**Feature Template** - Similar structure at feature level

**Story Template** - Similar structure at story level

---

## 14. AUTOMATION & TOOLING

### 14.1 Recommended Tools

**Option 1: Obsidian** (Visual, non-technical friendly)
- Graph view for dependencies
- Kanban plugin for boards
- Dataview for queries
- Calendar for timeline

**Option 2: VS Code + Foam** (Developer-focused)
- Markdown editing
- Git integration
- Extensions for visualization

**Option 3: Both**
- Team uses VS Code
- Board uses Obsidian export

### 14.2 Automation Scripts

**Metrics Calculator** (`scripts/calculate_metrics.py`):
```python
import os, re
from pathlib import Path

def parse_epics():
    total_sp = completed_sp = 0
    for file in Path("epics").glob("*.md"):
        content = file.read_text()
        if m := re.search(r'story_points_total: (\d+)', content):
            total_sp += int(m.group(1))
        if m := re.search(r'story_points_completed: (\d+)', content):
            completed_sp += int(m.group(1))
    
    print(f"Completion: {completed_sp/total_sp*100:.1f}% ({completed_sp}/{total_sp} SP)")

if __name__ == "__main__":
    parse_epics()
```

**Board Generator** (`scripts/generate_board.py`):
```python
from pathlib import Path
import yaml

def generate_epic_board():
    epics = []
    for file in Path("epics").glob("*.md"):
        content = file.read_text()
        if content.startswith("---"):
            yaml_str = content.split("---")[1]
            epics.append(yaml.safe_load(yaml_str))
    
    # Sort and generate board
    with open("boards/board-epic-view.md", "w") as f:
        f.write("# Board View

")
        for epic in sorted(epics, key=lambda e: e.get('status')):
            f.write(f"## {epic['epic_name']}
")
            f.write(f"Progress: {epic.get('completion_percentage', 0)}%

")
```

---

## 15. IMPLEMENTATION ROADMAP

### Week 1: Setup (Nov 13-19)
- [ ] Create Git repo structure
- [ ] Setup templates
- [ ] Create initial 3-5 epics
- [ ] Install Obsidian/VS Code

### Week 2: Sprint 5 Migration (Nov 20-26)
- [ ] Migrate Sprint 5 stories to MD
- [ ] Create sprint board
- [ ] Daily updates during sprint
- [ ] Test workflow with team

### Week 3: Backlog Creation (Nov 27 - Dec 3)
- [ ] Create all EPD-E002 features
- [ ] Create Sprint 6 backlog stories
- [ ] Generate first board report
- [ ] Sprint 5 retrospective

### Week 4: Automation (Dec 4-10)
- [ ] Setup metrics scripts
- [ ] Setup board generation
- [ ] Test monthly reporting
- [ ] Train team

---

## 16. RECOMMENDATIONS

### 16.1 Success Criteria

**For Board:**
- Understand project status in <5 minutes
- Know when features are delivered
- Understand why technical work is needed

**For Team:**
- Know what to build each sprint
- Understand how work contributes to epics
- Have clear acceptance criteria

**For Eddie:**
- Generate board report in <30 minutes
- Quickly identify dependencies
- Real-time progress visibility

### 16.2 Eddie's Recommendations

1. **Start Small**
   - Begin with 3-5 epics
   - Test with Sprint 5
   - Add automation when stable

2. **Focus on Critical Path**
   - Prioritize: MIG-E002, SEC-E001, EPD-E002, COM-E001

3. **Make Technical Epics Clear**
   - Always include business justification
   - Calculate ROI where possible
   - Link to compliance requirements

4. **Weekly Rhythm**
   - Monday: Sprint planning
   - Daily: Standups + updates
   - Friday: Backlog refinement
   - Monthly: Board reporting

5. **Tool Stack**
   - Git for version control
   - Obsidian for visual editing
   - Python for automation
   - Azure DevOps (optional)

### 16.3 Risks & Mitigations

**Manual Overhead:**
- Mitigation: Daily update discipline, Git hooks, weekly audits

**Team Adoption:**
- Mitigation: Start with pilot, show value, make optional initially

**Scalability:**
- Mitigation: Good tagging, Obsidian graph view, lightweight tools

### 16.4 Alternative: Hybrid Approach

**Option A: MD for Board, Azure DevOps for Team**
- Pros: Best of both worlds
- Cons: Eddie syncs both systems

**Option B: Azure DevOps + MD Export**
- Pros: Single source of truth
- Cons: Azure DevOps dependency

**Option C: Pure Azure DevOps + Dashboards**
- Pros: Fully integrated
- Cons: Vendor lock-in, cost

### 16.5 Final Recommendation

```
PHASE 1 (Week 1-4): MD-Based MVP
├── Setup structure
├── Create 5 critical epics
├── Run Sprint 5 in MD
└── Generate first report

Decision Point: Working?
├── YES → Phase 2
└── NO → Evaluate hybrid

PHASE 2 (Week 5-8): Scale Up
├── Add all epics
├── Create Q1 features
├── Setup automation
└── Train team

Decision Point: Adoption OK?
├── YES → Phase 3
└── NO → Consider hybrid

PHASE 3 (Week 9+): Optimize
├── CI/CD for boards
├── Metrics automation
├── Tool integration
└── Full coverage
```

**My Advice:**
1. Start pure MD (4 week pilot)
2. Evaluate after Sprint 6
3. Be ready to pivot if needed
4. Don't over-engineer early

---

## 17. APPENDIX

### 17.1 Glossary

- **Epic:** 50-150 SP, multiple sprints, board-visible
- **Feature:** 15-40 SP, 2-4 sprints, deliverable unit
- **Story:** 1-13 SP, 1 sprint, team backlog item
- **Sprint:** 2-week iteration
- **Velocity:** Avg SP completed per sprint
- **Technical Debt:** Suboptimal code needing refactoring
- **Critical Path:** Dependent items determining project duration

### 17.2 Story Point Scale

- **1 SP:** <2h, trivial
- **2 SP:** 2-4h, small
- **3 SP:** 4-8h, medium
- **5 SP:** 1-2 days, significant
- **8 SP:** 2-3 days, complex
- **13 SP:** 3-5 days, very complex
- **21+ SP:** Break down further

### 17.3 Common Pitfalls

1. **Vague Epics** → Use SMART criteria
2. **No Business Justification** → Always explain "why board cares"
3. **Untracked Dependencies** → Update weekly
4. **Large Stories** → Split if >13 SP
5. **Ignored DoD** → Use checklist
6. **Unclear Sprint Goal** → One sentence per sprint
7. **Technical Reports** → Translate to business outcomes
8. **Ignored Risks** → Weekly review

### 17.4 Useful Commands

```bash
# Count total SP
grep -r "story_points_total:" epics/ | awk '{sum+=$2} END {print sum}'

# Count completed SP
grep -r "story_points_completed:" epics/ | awk '{sum+=$2} END {print sum}'

# List blocked epics
grep -l "status: BLOCKED" epics/*.md

# Generate epic list
for file in epics/*.md; do
    name=$(grep "epic_name:" $file | cut -d'"' -f2)
    status=$(grep "status:" $file | awk '{print $2}')
    echo "$name - $status"
done
```

### 17.5 Quick Start Checklist

**Week 1:**
- [ ] Create repo
- [ ] Setup structure
- [ ] Copy templates
- [ ] Install tools
- [ ] Create 3 epics

**Week 2:**
- [ ] Document Sprint 5
- [ ] Create sprint board
- [ ] Daily updates
- [ ] Sprint review with MD board

**Week 3:**
- [ ] Add 5 more epics
- [ ] Create features
- [ ] Generate board report
- [ ] Retrospective on workflow

**Week 4:**
- [ ] Setup scripts
- [ ] Test automation
- [ ] Document workflow
- [ ] Train team
- [ ] Decision: continue/pivot?

---

## DOCUMENT CONTROL

**Version:** 1.0  
**Created:** 2025-11-12  
**Author:** Claude (for Eddie - ROSK Consulting)  
**Status:** READY FOR USE  
**Next Review:** After 4-week pilot

---

**Success with the implementation, Eddie! 🚀**

This roadmap gives you everything needed to setup a dual-view project management system with markdown files, combining traditional PM (for board) with agile/scrum (for team), specifically tailored for your HCI EPD modernization project.
