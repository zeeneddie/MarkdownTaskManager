# BMAD Method - Business Model Architecture & Design

**Status**: Placeholder - Waiting for repository clone
**Repository**: bmad-method (URL TBD)

## Overview

BMAD (Business Model Architecture & Design) is a methodology for systematic project definition through structured sessions.

## Session Types

### Green-Paper Session (Greenfield Projects)
For new development projects starting from scratch.

**Purpose**: Define vision, scope, and initial architecture
**Duration**: 2-4 hours
**Participants**: Product Owner, Architect, Key Stakeholders

**Key Questions**:
1. What is the business vision?
2. What problem are we solving?
3. Who are the stakeholders?
4. What are the guiding principles?
5. What is in scope? What is out of scope?
6. What are the constraints? (budget, timeline, technology)
7. What are the known risks?

**Output**: Green-paper document with vision, scope, principles, constraints, and risks

### Brown-Paper Session (Brownfield Projects)
For existing codebases requiring modernization or migration.

**Purpose**: Assess current state, technical debt, and migration strategy
**Duration**: 3-6 hours
**Participants**: Product Owner, Architect, Developers, QA

**Prerequisites**: Quality scan of existing codebase

**Key Questions**:
1. What is the current architecture? (from scan)
2. What is the technical debt? (from scan)
3. What are the security vulnerabilities? (from scan)
4. What must be preserved? (legacy constraints)
5. What needs improvement? (based on violations)
6. What is the migration strategy? (big-bang vs. incremental)
7. What are the risks? (technical, operational, business)

**Output**: Brown-paper document with current state, technical debt, migration plan, and risks

## Integration with Spec-Kit

BMAD sessions provide input for the Spec-Kit workflow:

```
BMAD Green-Paper → Constitution → Specification → Tasks
BMAD Brown-Paper → Constitution → Specification → Tasks (with scan data)
```

### Mapping:

**Green-Paper → Constitution**:
- Vision → Principles
- Stakeholders → Stakeholders
- Scope → Scope
- Constraints → Constraints
- Risks → Risks

**Brown-Paper → Constitution**:
- Current Architecture → Technical Context
- Technical Debt → Constraints
- Security Issues → Risks
- Migration Strategy → Constraints
- Scan Results → Quality Requirements

## TODO

- [ ] Clone bmad-method repository when URL available
- [ ] Clone bmad-expanded repository when URL available
- [ ] Study complete BMAD methodology documentation
- [ ] Adapt templates to full BMAD standard
- [ ] Implement BMAD-compliant quality gates
