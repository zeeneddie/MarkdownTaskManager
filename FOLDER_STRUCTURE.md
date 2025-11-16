# Multi-File Project Structure Specification

## Overview

The Project Manager uses a hierarchical folder structure where each level (Project, Epic, Feature, Story, Task) has its own folder with a markdown file containing metadata and content.

## Directory Structure

```
project-root/
├── project.md                          # Project overview and configuration
├── project-archive/                    # Archived items (maintains same structure)
│   └── epics/
│       └── EPIC-XXX-name/
└── epics/                              # Active epics
    └── EPIC-001-assessment/
        ├── epic.md                     # Epic metadata and description
        └── features/
            └── FEATURE-001-analysis/
                ├── feature.md          # Feature metadata
                └── stories/
                    └── STORY-001-metrics/
                        ├── story.md    # Story metadata
                        └── tasks/
                            ├── TASK-001.md
                            └── TASK-002.md
```

## Folder Naming Convention

Format: `{TYPE}-{ID}-{SLUG}`

- **TYPE**: EPIC, FEATURE, STORY, TASK
- **ID**: Zero-padded 3-digit number (001, 002, etc.)
- **SLUG**: Lowercase, hyphenated short name

Examples:
- `EPIC-001-assessment`
- `FEATURE-012-patient-search`
- `STORY-045-search-by-name`
- `TASK-123-frontend-component`

## File Formats

### project.md

```markdown
# Project: [Project Name]

**Status**: ACTIVE | ARCHIVED
**Start Date**: YYYY-MM-DD
**Target Date**: YYYY-MM-DD
**Owner**: @username

## Configuration

**Columns**: 📋 PLANNED (planned) | 🚀 IN PROGRESS (in-progress) | 🧪 TESTING (testing) | ✅ COMPLETED (completed)
**Priorities**: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW
**Types**: 📱 FUNCTIONAL, 🔧 TECHNICAL, 🔒 COMPLIANCE, 📊 REPORTING, 🏗️ INFRASTRUCTURE
**Phases**: INITIATIE, REALISATIE, IMPLEMENTATIE
**Users**: @user1 (Name), @user2 (Name)
**Tags**: #tag1, #tag2, #tag3

## Statistics

**Total Story Points**: 1500
**Completed Story Points**: 450
**Progress**: 30%
**Epics**: 12 total (3 completed, 5 in progress, 4 planned)

## Description

Project description and goals...

## Notes

General project notes...
```

### epic.md

```markdown
# EPIC-001 | Assessment & Architecture

**Type**: 🔧 TECHNICAL
**Priority**: 🟠 HIGH
**Status**: IN_PROGRESS
**Phase**: INITIATIE
**Owner**: @eddie
**Created**: 2025-11-01
**Target**: 2025-12-15

## Story Points

**Total**: 34
**Completed**: 13
**Progress**: 38%

## Dependencies

**Blocks**:
- `../EPIC-002-patient-dossier/`
- `../EPIC-003-medication/`

**Depends On**:
- None

## Business Value

Foundation for migration, provides risk identification and strategic direction for the entire modernization project.

## Goals & Acceptance Criteria

- [ ] Complete codebase analysis report
- [x] Architecture design document approved
- [ ] Migration strategy defined
- [ ] Risk register completed

## Features

Auto-aggregated from `./features/`:
- ✅ FEATURE-001: Codebase Analysis (13/13 SP)
- 🚀 FEATURE-002: Architecture Design (8/21 SP)

## Notes

Initial assessment shows 1.38M LOC with significant technical debt in authentication and database layers...

## Risks

- R001: Legacy database complexity (MEDIUM impact, MEDIUM probability)
- R002: Team capacity constraints (LOW impact, HIGH probability)
```

### feature.md

```markdown
# FEATURE-001 | Codebase Quality Analysis

**Parent**: `../../epic.md` (EPIC-001)
**Type**: Feature
**Priority**: 🟠 HIGH
**Status**: COMPLETED
**Owner**: @eddie
**Created**: 2025-11-05
**Started**: 2025-11-08
**Completed**: 2025-11-12

## Story Points

**Total**: 13
**Completed**: 13
**Progress**: 100%
**Estimated Sprints**: 1

## Description

Complete analysis of existing codebase quality, technical debt, and migration complexity including metrics, complexity analysis, and technical debt hotspots.

## Acceptance Criteria

- [x] Generate metrics report for entire codebase
- [x] Identify top 10 most complex modules
- [x] Document technical debt hotspots
- [x] Estimate migration effort per module

## Stories

Auto-aggregated from `./stories/`:
- ✅ STORY-001: Analyze code metrics (5/5 SP)
- ✅ STORY-002: Complexity analysis (8/8 SP)

## Dependencies

**Depends On**: None

## Notes

Used SonarQube for static analysis. Found 1.38M LOC across 3,500 files. Key findings:
- 72 SQL injection vulnerabilities
- 43 XSS vulnerabilities
- Average cyclomatic complexity: 8.2
```

### story.md

```markdown
# STORY-001 | Analyze code metrics and complexity

**Parent**: `../../feature.md` (FEATURE-001)
**Type**: Story
**Priority**: 🟠 HIGH
**Status**: COMPLETED
**Sprint**: Sprint 1
**Assigned**: @eddie
**Created**: 2025-11-05
**Started**: 2025-11-08
**Completed**: 2025-11-10

## Story Points

**SP**: 5

## User Story

As a technical lead
I want to analyze code metrics (LOC, complexity, dependencies)
So that I understand the scope and complexity of the migration

## Acceptance Criteria

- [x] Setup code analysis tools (SonarQube, NDepend)
- [x] Run metrics on entire codebase
- [x] Generate comprehensive metrics report
- [x] Identify top 10 most complex modules

## Tasks

Auto-aggregated from `./tasks/`:
- ✅ TASK-001: Setup analysis tools (4h)
- ✅ TASK-002: Run metrics scan (2h)
- ✅ TASK-003: Analyze results (6h)
- ✅ TASK-004: Create report (4h)

## Definition of Done

- [x] Code complete and committed
- [x] All acceptance criteria validated
- [x] Documentation updated
- [x] Demo to PO approved

## Notes

**Result**:
Generated comprehensive metrics report. Codebase consists of 1.38M LOC across 3,500 files.

**Key Findings**:
- Average cyclomatic complexity: 8.2 (target: <5)
- Top complex module: AuthenticationLibrary (complexity 45)
- 25% of codebase is technical debt

**Decisions**:
- Use SonarQube as primary analysis tool
- Focus refactoring on top 10 complex modules first
```

### TASK-001.md

```markdown
# TASK-001 | Setup code analysis tools

**Parent**: `../story.md` (STORY-001)
**Type**: Task
**Status**: COMPLETED
**Assigned**: @eddie
**Hours**: 4
**Created**: 2025-11-08
**Completed**: 2025-11-08

## Description

Install and configure SonarQube and NDepend for codebase analysis.

## Steps

- [x] Install SonarQube server locally
- [x] Configure project in SonarQube
- [x] Install NDepend plugin for Visual Studio
- [x] Setup initial analysis profiles

## Notes

SonarQube setup completed. Server running on localhost:9000. Created project "HCI-EPD-Legacy" with C# and JavaScript analyzers enabled.

NDepend configured with custom rules for legacy ASP.NET code patterns.

## Time Tracking

- Actual: 4h
- Estimated: 4h
- Variance: 0h
```

## File Relationships

### Parent References

Use relative paths to reference parent items:
- From feature.md: `../../epic.md`
- From story.md: `../../feature.md`
- From task.md: `../story.md`

### Child References

Children are auto-discovered by scanning subdirectories:
- Epic children: `./features/*/feature.md`
- Feature children: `./stories/*/story.md`
- Story children: `./tasks/*.md`

### Dependency References

Use relative or absolute paths from project root:
- Same level: `../EPIC-002-patient-dossier/`
- Cross-epic: `../../EPIC-005-security/features/FEATURE-012-auth/`

## Auto-Aggregation Rules

### Story Points

Story points automatically roll up from children:
- Epic SP = Sum of all Feature SP
- Feature SP = Sum of all Story SP
- Story SP = Manually set (not from tasks)

### Progress Calculation

Progress = (Completed SP / Total SP) * 100

### Status Propagation

- Epic status = IN_PROGRESS if any feature IN_PROGRESS
- Epic status = COMPLETED if all features COMPLETED
- Same logic applies down the hierarchy

## Special Folders

### project-archive/

Maintains same structure as active project. To archive:
1. Move entire epic folder: `epics/EPIC-XXX/` → `project-archive/epics/EPIC-XXX/`
2. Update any dependency references in remaining epics

## Metadata Parsing

### Common Fields (All Levels)

- **Type**: EPIC | FEATURE | STORY | TASK
- **Status**: PLANNED | IN_PROGRESS | BLOCKED | TESTING | COMPLETED
- **Priority**: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🟢 LOW
- **Owner/Assigned**: @username
- **Created**: YYYY-MM-DD
- **Started**: YYYY-MM-DD (optional)
- **Due**: YYYY-MM-DD (optional)
- **Completed**: YYYY-MM-DD (optional)

### Epic-Specific

- **Phase**: INITIATIE | REALISATIE | IMPLEMENTATIE
- **Type**: 📱 FUNCTIONAL | 🔧 TECHNICAL | 🔒 COMPLIANCE | etc.
- **Dependencies**: List of paths to other epics

### Story-Specific

- **Sprint**: Sprint name
- **Story Points**: Number
- **User Story**: As a... I want... So that...
- **Acceptance Criteria**: Checklist

### Task-Specific

- **Hours**: Estimated/actual time
- **Steps**: Checklist of work items

## Implementation Notes

### Loading Strategy

1. **Initial load**: Only read project.md and list epic folders
2. **Drill-down**: On clicking epic, read epic.md and list feature folders
3. **Breadcrumb up**: Cache loaded levels for quick navigation

### Caching

- Keep parsed metadata in memory for recently accessed items
- Cache expires after 5 minutes or on explicit refresh
- Invalidate cache when saving changes

### Performance

- Lazy load children (don't read all files on startup)
- Use directory listing before reading files
- Implement virtual scrolling for large lists (100+ items)

## Migration from Single-File

To convert existing `project.md` to multi-file:

1. Parse single file into hierarchy
2. Create folder structure
3. Split content into individual files
4. Generate dependency references
5. Validate all references work

Script: `scripts/migrate-to-multifile.js`
