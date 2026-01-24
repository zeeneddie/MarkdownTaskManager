# MarQed.ai Workflows Documentation

**Complete guide to MarQed.ai AI-driven development workflows**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Workflow Types](#workflow-types)
3. [Bug Fix Workflow](#bug-fix-workflow)
4. [Feature Changes Workflow](#feature-changes-workflow)
5. [Migration Workflow](#migration-workflow)
6. [Parallel Execution](#parallel-execution)
7. [Task Integration](#task-integration)
8. [Validation & Quality](#validation--quality)
9. [WBSO Reporting](#wbso-reporting)
10. [Best Practices](#best-practices)

---

## Overview

MarQed.ai provides three specialized workflows for AI-driven software development:

| Workflow | Purpose | Duration | Parallelizable |
|----------|---------|----------|----------------|
| **Bug Fix** | Root cause analysis & safe fixes | 2-8 hours | No |
| **Feature Changes** | New features & enhancements | 8-40 hours | Yes |
| **Migration** | Legacy code modernization | 200-400 hours | Partial |

All workflows follow the **MarQed.ai Loop**:
```
Initialize → Load Context → Execute Task → Validate → 
Update State → Browser Validation → Report → Next Cycle
```

---

## Workflow Types

### 1. Bug Fix Workflow

**Purpose**: Quickly diagnose and fix bugs with comprehensive testing

**Phases**: 7 sequential phases
**Script**: `workflows/marqed-bugfix.sh`
**Template**: `templates/BUG-TEMPLATE-v2.md`
**Prompt**: `templates/prompts/prompt-bugfix.md`

**Key Features**:
- Root cause verification
- Regression prevention
- Comprehensive testing
- Fast turnaround

### 2. Feature Changes Workflow

**Purpose**: Implement new features with parallel execution support

**Phases**: 6 phases (some parallelizable)
**Script**: `workflows/marqed-changes.sh`
**Template**: `templates/CHANGE-TEMPLATE-v2.md`
**Prompt**: `templates/prompts/prompt-changes.md`

**Key Features**:
- Parallel feature development
- Multi-session coordination
- Comprehensive testing
- Documentation integration

### 3. Migration Workflow

**Purpose**: Systematically migrate legacy code to modern stacks

**Phases**: 9 sequential phases
**Script**: `workflows/marqed-migration.sh`
**Template**: `templates/MIGRATION-TEMPLATE-v2.md`
**Prompt**: `templates/prompts/prompt-migration.md`

**Key Features**:
- Comprehensive analysis
- Phased execution
- Security compliance
- Risk mitigation

---

## Bug Fix Workflow

### Quick Start
```bash
# 1. Create PRD from template
cp templates/BUG-TEMPLATE-v2.md ./PRD.md
# Edit PRD with bug details

# 2. Run workflow
./workflows/marqed-bugfix.sh \
  --id BUG-2026-01-23-001 \
  --prd ./PRD.md \
  --context ./src
```

### Phases

#### Phase 1: Root Cause Verification (~30 min)
- Reproduce the bug
- Analyze logs and stack traces
- Trace code path
- Document root cause

**Validation**:
- Root cause clearly identified
- Supporting evidence collected
- Code path understood

#### Phase 2: Fix Implementation (~2 hours)
- Design minimal fix
- Implement changes
- Follow code standards
- Add error handling

**Validation**:
- Fix is minimal and targeted
- Code quality maintained
- No new bugs introduced

#### Phase 3: Unit Testing (~1 hour)
- Write test reproducing bug
- Verify test fails without fix
- Verify test passes with fix
- Add edge case tests

**Validation**:
- Test would have caught bug
- Covers specific scenario
- Includes edge cases

#### Phase 4: Integration Testing (~1 hour)
- Run full test suite
- Verify dependent modules
- Check performance
- Test interactions

**Validation**:
- All existing tests pass
- No integration issues
- Performance acceptable

#### Phase 5: Regression Testing (~1.5 hours)
- Run comprehensive suite
- Check for side effects
- Monitor resources
- Verify stability

**Validation**:
- Full regression passes
- No new failures
- Performance stable

#### Phase 6: Code Review & Documentation (~45 min)
- Self-review changes
- Update documentation
- Add changelog entry
- Prepare for review

**Validation**:
- Code is clear
- Documentation updated
- Changelog added

#### Phase 7: Deployment Preparation (~30 min)
- Create deployment package
- Document deployment steps
- Create rollback plan
- Define monitoring

**Validation**:
- Package ready
- Steps documented
- Rollback planned

### Total Duration

**Estimated**: 7.25 hours  
**Typical Range**: 4-12 hours depending on complexity

### Example
```bash
# Bug: Login accepts any password

# 1. Create PRD
cat > PRD.md << 'EOF'
## Bug Description
Login endpoint accepts any password for valid users

## Root Cause
Password validation check is missing in auth service

## Solution
Add bcrypt password comparison before generating token
EOF

# 2. Run workflow
./workflows/marqed-bugfix.sh --id BUG-001 --prd PRD.md

# 3. Monitor progress
./workflows/common/monitor-tasks.sh BUG-001

# 4. Review results
cat ~/.marqed/logs/BUG-001/WBSO-REPORT.md
```

---

## Feature Changes Workflow

### Quick Start
```bash
# 1. Create PRD from template
cp templates/CHANGE-TEMPLATE-v2.md ./PRD.md
# Edit PRD with feature requirements

# 2. Run workflow (single session)
./workflows/marqed-changes.sh \
  --id CHANGE-2026-01-23-001 \
  --prd ./PRD.md \
  --context ./src

# OR run with parallel execution
./workflows/marqed-changes.sh \
  --id CHANGE-2026-01-23-001 \
  --prd ./PRD.md \
  --context ./src \
  --parallel 3
```

### Phases

#### Phase 1: Design & Architecture (~4 hours)
- Review requirements
- Design solution
- Plan data models
- Identify integration points

**Validation**:
- Design addresses requirements
- Integration points identified
- Data models sound

**Parallelizable**: ❌ No (foundation)

#### Phase 2: Feature Implementation (~variable)
- Multiple parallelizable tasks
- Each feature independent
- Follow design specifications
- Maintain code quality

**Validation**:
- Code implements design
- Follows conventions
- Handles errors

**Parallelizable**: ✅ Yes (if features independent)

#### Phase 3: Unit Testing (~variable)
- Multiple parallelizable test suites
- Comprehensive coverage
- Edge case testing
- Clear test documentation

**Validation**:
- Tests cover all paths
- Tests are clear
- High coverage

**Parallelizable**: ✅ Yes (different test files)

#### Phase 4: Integration Testing (~3 hours)
- Integrate all features
- Test interactions
- Verify API contracts
- Check performance

**Validation**:
- Features work together
- No conflicts
- Performance acceptable

**Parallelizable**: ❌ No (requires all features)

#### Phase 5: End-to-End Testing (~4 hours)
- Complete user workflows
- UI/UX verification
- Error scenarios
- Data persistence

**Validation**:
- All workflows function
- Acceptance criteria met
- UX is smooth

**Parallelizable**: ⚠️ Partial (different workflows)

#### Phase 6: Documentation & Review (~3 hours)
- Technical documentation
- User documentation
- API docs
- Changelog

**Validation**:
- All features documented
- API docs complete
- Changelog updated

**Parallelizable**: ✅ Yes (different docs)

### Parallel Execution Example
```bash
# Scenario: 3 independent features

# PRD contains:
# - Feature A: User management
# - Feature B: Role management
# - Feature C: Permission system

# Run with 3 parallel sessions
./workflows/marqed-changes.sh \
  --id CHANGE-001 \
  --parallel 3

# What happens:
# Session A: Implements Feature A
# Session B: Implements Feature B
# Session C: Implements Feature C
# All coordinate through shared task list

# Monitor all sessions
./workflows/common/monitor-tasks.sh CHANGE-001

# Results:
# - 3x faster for parallelizable phases
# - Sequential phases still run single-threaded
# - Final integration brings everything together
```

### Total Duration

**Estimated**: 20-60 hours depending on scope  
**With 3 parallel sessions**: Can reduce by 40-60% for parallelizable phases

---

## Migration Workflow

### Quick Start
```bash
# 1. Create PRD from template
cp templates/MIGRATION-TEMPLATE-v2.md ./PRD.md
# Edit PRD with migration scope

# 2. Run workflow
./workflows/marqed-migration.sh \
  --id MIG-2026-01-23-HCI \
  --prd ./PRD.md \
  --source ./legacy/asp-classic \
  --target ./modern/dotnet-core
```

### Phases

#### Phase 1: Analysis & Planning (~40 hours)
- Analyze legacy codebase
- Identify dependencies
- Plan migration strategy
- Assess risks

#### Phase 2: Environment Setup (~24 hours)
- Setup modern toolchain
- Configure build system
- Establish testing framework
- Setup CI/CD

#### Phase 3: Data Migration (~48 hours)
- Migrate database schema
- Transform data formats
- Validate data integrity
- Test data access

#### Phase 4: Core Migration (~64 hours)
- Migrate business logic
- Transform algorithms
- Update APIs
- Maintain functionality

#### Phase 5: UI Migration (~40 hours)
- Migrate presentation layer
- Update user interfaces
- Ensure UX consistency
- Test interactions

#### Phase 6: Integration (~32 hours)
- Integrate all components
- Test system interactions
- Verify data flow
- Performance testing

#### Phase 7: Testing (~48 hours)
- Comprehensive test suite
- Regression testing
- Performance benchmarks
- User acceptance testing

#### Phase 8: Security & Compliance (~32 hours)
- Security hardening
- Compliance verification (NEN7510, ISO27001)
- Penetration testing
- Audit preparation

#### Phase 9: Deployment (~24 hours)
- Deployment preparation
- Production deployment
- Monitoring setup
- Documentation

### Total Duration

**Estimated**: 352 hours (~9 weeks)  
**Typical Range**: 300-500 hours depending on scope

### Example
```bash
# Migration: ASP Classic → .NET Core

# 1. Analyze legacy
./workflows/marqed-migration.sh \
  --id MIG-HCI-EPD \
  --source /legacy/hci-epd \
  --target /modern/hci-epd-core

# 2. Monitor progress
watch -n 60 './workflows/common/monitor-tasks.sh MIG-HCI-EPD'

# 3. Review migration summary
cat ~/.marqed/logs/MIG-HCI-EPD/MIGRATION-SUMMARY.md

# 4. Check WBSO report
cat ~/.marqed/logs/MIG-HCI-EPD/WBSO-REPORT.md
```

---

## Parallel Execution

### When to Use Parallel Execution

Use parallel execution for **Feature Changes** when:

✅ **Good candidates**:
- Multiple independent features
- Different modules/components
- Separate test suites
- Different documentation sections

❌ **Not suitable for**:
- Bug fixes (sequential by nature)
- Integration work (requires all pieces)
- Migrations (mostly sequential)
- Single complex features

### How It Works
```bash
# Start parallel execution
./workflows/marqed-changes.sh \
  --id CHANGE-001 \
  --parallel 3

# Behind the scenes:
# 1. spawn-parallel-sessions.sh spawns 3 sessions
# 2. Each session gets unique ID (A, B, C)
# 3. All share same task list: ~/.claude/tasks/CHANGE-001.json
# 4. Sessions coordinate through task status updates
# 5. Each picks available parallelizable tasks
# 6. Final integration runs single-threaded
```

### Coordination Mechanism

**Task Selection**:
```javascript
// Each session independently picks tasks
availableTasks = tasks.filter(task => 
  task.status === 'pending' &&
  task.parallelizable === true &&
  allDependenciesMet(task)
);

// Pick first available
myTask = availableTasks[0];

// Mark as mine
myTask.status = 'in_progress';
myTask.notes = `Session ${SESSION_ID}`;
```

**Conflict Avoidance**:
- Sessions check status before starting
- Atomic updates prevent race conditions
- Notes field identifies session owner
- Other sessions skip in-progress tasks

### Monitoring Parallel Execution
```bash
# Real-time monitoring
./workflows/common/monitor-tasks.sh CHANGE-001

# Output shows:
# - Total progress
# - Tasks by session
# - Current activities
# - Blockers

# Example:
#   Session A: ✅ Feature A complete
#   Session B: 🔄 Feature B in progress
#   Session C: ⏳ Waiting for dependencies
```

---

## Task Integration

### Task Lifecycle in Workflows

1. **Initialization**:
```bash
   ./scripts/prd-to-tasks.sh WORKFLOW-001 PRD.md
   # Creates: ~/.claude/tasks/WORKFLOW-001.json
```

2. **Execution**:
```bash
   export CLAUDE_CODE_TASK_LIST_ID="WORKFLOW-001"
   claude-code --task-list WORKFLOW-001 --context ./src
```

3. **Progress Updates**:
```javascript
   // Tasks automatically update as work progresses
   task.status = 'in_progress';  // Started
   task.status = 'completed';    // Finished
   task.status = 'blocked';      // Stuck
```

4. **Synchronization**:
```bash
   ./workflows/common/sync-tasks-to-prd.sh \
     ~/.claude/tasks/WORKFLOW-001.json \
     PRD.md
   # Updates "Passes: false" → "Passes: true"
```

### Task Structure in Workflows

**Bug Fix Tasks**:
```json
{
  "id": "bug-phase1-verify",
  "title": "Verify root cause",
  "parallelizable": false,  // Sequential workflow
  "dependencies": []
}
```

**Feature Change Tasks**:
```json
{
  "id": "change-phase2-implement-feature-a",
  "title": "Implement user management",
  "parallelizable": true,   // Can run in parallel
  "dependencies": ["change-phase1-design"]
}
```

**Migration Tasks**:
```json
{
  "id": "mig-phase3-data",
  "title": "Migrate data layer",
  "parallelizable": false,  // Sequential phases
  "dependencies": ["mig-phase2-setup"],
  "estimatedTime": "48h"   // Large tasks
}
```

---

## Validation & Quality

### Automated Validation

Each workflow includes validation:
```bash
# Phase validation
./workflows/common/validation.sh validate_current_phase \
  PRD.md \
  ./src

# Task validation
./workflows/common/validation.sh validate_task_complete \
  ~/.claude/tasks/WORKFLOW-001.json \
  task-123 \
  ./src

# Full validation suite
./workflows/common/validation.sh run_full_validation \
  PRD.md \
  ~/.claude/tasks/WORKFLOW-001.json \
  ./src
```

### Validation Criteria

**Bug Fixes**:
- Root cause documented
- Fix implements solution
- Tests prevent regression
- All tests pass
- No new bugs introduced

**Feature Changes**:
- Design addresses requirements
- Code follows standards
- High test coverage (>80%)
- Integration works
- Documentation complete

**Migrations**:
- Analysis comprehensive
- Functionality preserved
- Security improved
- Performance acceptable
- Compliance verified

### Quality Gates

Workflows enforce quality gates:
```bash
# Cannot proceed to next phase unless:
# 1. All phase tasks completed
# 2. Validation passes
# 3. Tests pass
# 4. No critical blockers

# Example:
if ! validate_current_phase PRD.md ./src; then
  echo "❌ Validation failed - cannot proceed"
  exit 1
fi
```

---

## WBSO Reporting

### Automatic Report Generation

All workflows generate WBSO R&D reports:
```bash
# Generated automatically on completion
~/.marqed/logs/${WORKFLOW_ID}/WBSO-REPORT.md
```

### Report Contents

**Standard Sections**:
1. Project summary
2. Activities performed (from tasks)
3. Time investment
4. Innovation elements
5. R&D justification
6. Compliance information

**Example Report**:
```markdown
# WBSO R&D Report - Bug Fix

**Project**: MarQed.ai Bug Fix
**Bug ID**: BUG-2026-01-23-001
**Date**: 2026-01-23

## Activities Performed

### Root Cause Verification
**Duration**: 30m
**R&D Activities**:
- Systematic investigation using advanced debugging
- Root cause analysis methodology
- Novel diagnostic approach

### Fix Implementation
**Duration**: 2h
**R&D Activities**:
- Solution design
- Technical innovation
- Code transformation

## Time Investment
**Total**: 7.25 hours

## Innovation Elements
1. Root cause analysis techniques
2. Automated validation
3. Testing methodology
4. Knowledge capture

## Compliance
Qualifies for WBSO under:
- Technical uncertainty resolution
- Systematic investigation
- New knowledge generation
```

### Using Reports
```bash
# View report
cat ~/.marqed/logs/BUG-001/WBSO-REPORT.md

# Include in WBSO application
# Reports document:
# - R&D activities
# - Time investment
# - Innovation elements
# - Technical challenges

# For multiple workflows:
cat ~/.marqed/logs/*/WBSO-REPORT.md > WBSO-2026-Q1.md
```

---

## Best Practices

### 1. Start with Good PRDs

✅ **Good PRD**:
- Clear objectives
- Detailed requirements
- Well-defined validation criteria
- Realistic estimates
- Proper task breakdown

❌ **Bad PRD**:
- Vague requirements
- Missing acceptance criteria
- Unrealistic estimates
- Poor task granularity

### 2. Monitor Progress Actively
```bash
# Check progress regularly
./workflows/common/monitor-tasks.sh WORKFLOW-001

# Watch for blockers
./workflows/common/loop-core.sh --blockers WORKFLOW-001

# Review logs
tail -f ~/.marqed/logs/WORKFLOW-001/*.log
```

### 3. Handle Blockers Quickly

When tasks get blocked:
1. Identify root cause
2. Document in task notes
3. Escalate if needed
4. Update stakeholders
5. Find workarounds

### 4. Use Parallel Execution Wisely

**When to parallelize**:
- 3+ independent features
- Large codebase
- Experienced with workflows
- Good task breakdown

**When to stay sequential**:
- Single feature
- Small changes
- Learning the system
- Tight integration

### 5. Validate Continuously

Don't wait until the end:
- Validate after each phase
- Run tests frequently
- Check code quality
- Review progress

### 6. Document as You Go

- Update PRD with findings
- Add notes to tasks
- Document decisions
- Capture learnings

### 7. Learn from Reports

After each workflow:
- Review WBSO report
- Analyze metrics
- Identify improvements
- Update estimates

---

## Troubleshooting

### Workflow Won't Start

**Check**:
1. PRD file exists and is valid
2. Task list created successfully
3. Context directory accessible
4. Claude Code installed
```bash
# Debug initialization
./scripts/prd-to-tasks.sh WORKFLOW-001 PRD.md --verbose
```

### Tasks Not Progressing

**Check**:
1. Dependencies satisfied
2. No circular dependencies
3. Task not blocked
4. Claude Code running
```bash
# Check task status
./workflows/common/monitor-tasks.sh WORKFLOW-001

# Check dependencies
jq '.tasks[] | {id, status, dependencies}' \
  ~/.claude/tasks/WORKFLOW-001.json
```

### Parallel Sessions Conflicting

**Check**:
1. Tasks properly marked parallelizable
2. No file conflicts
3. Atomic task updates
4. Session coordination working
```bash
# Check which sessions active
jq '.tasks[] | select(.status == "in_progress") | .notes' \
  ~/.claude/tasks/WORKFLOW-001.json
```

### Validation Failing

**Check**:
1. Criteria realistic
2. Work actually complete
3. Tests passing
4. Files in right location
```bash
# Run validation manually
./workflows/common/validation.sh validate_current_phase \
  PRD.md ./src --verbose
```

---

## Additional Resources

- **Templates**: `templates/*.md`
- **Prompts**: `templates/prompts/*.md`
- **Scripts**: `workflows/*.sh` and `scripts/*.sh`
- **Settings**: `settings/*.json`
- **Task Guide**: `CLAUDE-CODE-TASKS-GUIDE.md`

---

**Workflows Version**: 2.0  
**Last Updated**: January 23, 2026  
**Methodology**: MarQed.ai AI-Driven Development

---

**Master the workflows, deliver with confidence. Happy coding!** 🚀✨