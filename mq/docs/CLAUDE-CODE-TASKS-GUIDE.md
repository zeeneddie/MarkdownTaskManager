	# Claude Code Tasks Integration Guide

**Complete guide to using Claude Code tasks within the MarQed.ai workflow system**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What Are Claude Code Tasks?](#what-are-claude-code-tasks)
3. [How MarQed.ai Uses Tasks](#how-marqedai-uses-tasks)
4. [Task Structure](#task-structure)
5. [Task Lifecycle](#task-lifecycle)
6. [Creating Task Lists](#creating-task-lists)
7. [Parallel Execution](#parallel-execution)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Examples](#examples)

---

## Overview

Claude Code Tasks provide **persistence and coordination** for AI-driven development workflows. MarQed.ai uses this system to:

- ✅ Track progress across multiple sessions
- ✅ Enable parallel task execution
- ✅ Maintain state between iterations
- ✅ Coordinate multiple Claude Code instances
- ✅ Generate comprehensive WBSO reports

---

## What Are Claude Code Tasks?

Claude Code Tasks are a **structured task management system** integrated into Claude Code:
```json
{
  "id": "task-list-123",
  "created": "2026-01-23T10:00:00Z",
  "tasks": [
    {
      "id": "task-1",
      "title": "Implement user authentication",
      "description": "Create JWT-based auth with refresh tokens",
      "status": "completed",
      "dependencies": [],
      "estimatedTime": "4h",
      "parallelizable": false
    }
  ]
}
```

**Stored Location**: `~/.claude/tasks/${TASK_LIST_ID}.json`

**Key Features**:
- Persistent across sessions
- Dependency tracking
- Status management
- Parallel execution support
- Progress tracking

---

## How MarQed.ai Uses Tasks

### 1. Initialization

PRDs are converted to task lists:
```bash
./scripts/prd-to-tasks.sh BUG-2026-01-23-001 ./PRD.md
```

**Output**: `~/.claude/tasks/BUG-2026-01-23-001.json`

### 2. Execution

Workflows execute tasks sequentially or in parallel:
```bash
# Single session
./workflows/marqed-bugfix.sh --id BUG-2026-01-23-001

# Parallel sessions
./workflows/marqed-changes.sh --id CHANGE-2026-01-23-001 --parallel 3
```

### 3. Coordination

Tasks coordinate through shared state:
```json
{
  "id": "feature-a",
  "status": "in_progress",
  "notes": "Session A working on this"
}
```

Other sessions see this and pick different tasks.

### 4. Completion

When all tasks complete:
- PRD is updated (`Passes: true`)
- WBSO report is generated
- Summary is created

---

## Task Structure

### Required Fields
```json
{
  "id": "unique-identifier",           // REQUIRED: Unique task ID
  "title": "Human-readable title",     // REQUIRED: Short description
  "description": "Detailed description", // REQUIRED: What to do
  "status": "pending",                 // REQUIRED: Current status
  "dependencies": [],                  // REQUIRED: Task IDs this depends on
  "estimatedTime": "2h",              // REQUIRED: Time estimate
  "parallelizable": false             // REQUIRED: Can run in parallel?
}
```

### Optional Fields
```json
{
  "phase": 1,                         // Phase number
  "priority": "high",                 // Priority level
  "assignee": "Session A",            // Who's working on it
  "startedAt": "2026-01-23T10:00:00Z", // When work started
  "completedAt": "2026-01-23T12:00:00Z", // When completed
  "notes": "Additional information",  // Free-form notes
  "tags": ["auth", "security"]       // Categorization
}
```

### Status Values

- `pending`: Not started, waiting for dependencies
- `in_progress`: Currently being worked on
- `completed`: Successfully finished
- `blocked`: Cannot proceed (external blocker)

---

## Task Lifecycle

### 1. Creation

Tasks start as `pending`:
```json
{
  "id": "auth-implement",
  "status": "pending",
  "dependencies": ["auth-design"]
}
```

### 2. Availability

Task becomes available when:
- Status is `pending`
- All dependencies are `completed`
```javascript
// Check if task is available
const isAvailable = (task, allTasks) => {
  if (task.status !== 'pending') return false;
  
  return task.dependencies.every(depId => {
    const dep = allTasks.find(t => t.id === depId);
    return dep && dep.status === 'completed';
  });
};
```

### 3. Execution

Session picks task and marks `in_progress`:
```json
{
  "id": "auth-implement",
  "status": "in_progress",
  "startedAt": "2026-01-23T10:30:00Z",
  "notes": "Session A - Implementing JWT service"
}
```

### 4. Completion

Session finishes and marks `completed`:
```json
{
  "id": "auth-implement",
  "status": "completed",
  "completedAt": "2026-01-23T14:30:00Z",
  "notes": "JWT service implemented with refresh tokens"
}
```

### 5. Blocking

If task cannot proceed:
```json
{
  "id": "deploy",
  "status": "blocked",
  "notes": "Staging environment unavailable"
}
```

---

## Creating Task Lists

### From PRD (Automated)

Use the `prd-to-tasks.sh` script:
```bash
./scripts/prd-to-tasks.sh BUG-2026-01-23-001 ./PRD.md
```

**How it works**:
1. Parses PRD.md for phases
2. Extracts task JSON from each phase
3. Combines into single task list
4. Validates dependencies
5. Writes to `~/.claude/tasks/`

### Manual Creation

Create JSON directly:
```bash
cat > ~/.claude/tasks/TEST-001.json << 'EOF'
{
  "id": "TEST-001",
  "created": "2026-01-23T10:00:00Z",
  "tasks": [
    {
      "id": "test-1",
      "title": "Write unit tests",
      "description": "Test authentication module",
      "status": "pending",
      "dependencies": [],
      "estimatedTime": "2h",
      "parallelizable": true
    }
  ]
}
EOF
```

### Validation

Validate task list structure:
```bash
# Check JSON is valid
jq empty ~/.claude/tasks/TEST-001.json

# Check all dependencies exist
jq -r '.tasks[] | .dependencies[]' ~/.claude/tasks/TEST-001.json | \
  while read dep; do
    if ! jq -e ".tasks[] | select(.id == \"$dep\")" ~/.claude/tasks/TEST-001.json > /dev/null; then
      echo "Missing dependency: $dep"
    fi
  done
```

---

## Parallel Execution

### Enabling Parallelization

Mark tasks as parallelizable:
```json
{
  "id": "feature-a",
  "title": "Implement feature A",
  "parallelizable": true,  // Can run in parallel
  "dependencies": ["design"]
}
```

### Running Parallel Sessions

Spawn multiple sessions:
```bash
./workflows/marqed-changes.sh \
  --id CHANGE-2026-01-23-001 \
  --parallel 3
```

**What happens**:
1. Script spawns 3 Claude Code sessions
2. All share same task list ID
3. Each picks available parallelizable tasks
4. Coordination happens through task status

### Task Selection Logic

Each session:
```javascript
// Prefer parallelizable tasks
const availableTasks = tasks.filter(t => 
  t.status === 'pending' &&
  t.parallelizable === true &&
  allDependenciesMet(t)
);

// Pick first available
const task = availableTasks[0];

// Mark in progress
task.status = 'in_progress';
task.notes = `Session ${SESSION_ID} working`;
```

### Avoiding Conflicts

Sessions avoid conflicts by:
1. Checking task status before starting
2. Atomically updating status to `in_progress`
3. Adding session ID to notes
4. Picking different tasks

**Bad**:
```javascript
// Don't do this - race condition!
if (task.status === 'pending') {
  // Another session might start here
  task.status = 'in_progress';
}
```

**Good**:
```javascript
// Atomic operation with jq
jq '(.tasks[] | select(.id == "task-1" and .status == "pending")) |= 
  (.status = "in_progress" | .notes = "Session A")' \
  tasks.json > tasks.json.tmp && mv tasks.json.tmp tasks.json
```

---

## Troubleshooting

### Tasks Not Updating

**Problem**: Changes to tasks.json not persisting

**Solutions**:
1. Check file permissions:
```bash
   ls -la ~/.claude/tasks/
```

2. Verify atomic writes:
```bash
   # Always use tmp file + mv
   jq '...' tasks.json > tasks.json.tmp
   mv tasks.json.tmp tasks.json
```

3. Check for locked files:
```bash
   lsof ~/.claude/tasks/TASK-001.json
```

### Circular Dependencies

**Problem**: Task A depends on B, B depends on A

**Detection**:
```bash
# Find circular dependencies
./scripts/validate-tasks.sh TASK-001.json
```

**Solution**: Break the cycle by removing one dependency

### Stuck Tasks

**Problem**: Task marked `in_progress` but session died

**Solution**: Manually reset:
```bash
jq '(.tasks[] | select(.id == "stuck-task")) |= 
  (.status = "pending" | del(.startedAt) | .notes = "Reset after session failure")' \
  ~/.claude/tasks/TASK-001.json > tasks.json.tmp
mv tasks.json.tmp ~/.claude/tasks/TASK-001.json
```

### Missing Dependencies

**Problem**: Task depends on non-existent task

**Detection**:
```bash
jq -r '.tasks[] | 
  .dependencies[] as $dep | 
  if ([.tasks[] | .id] | contains([$dep]) | not) 
  then "Missing: \($dep)" 
  else empty end' tasks.json
```

**Solution**: Either add the missing task or remove the dependency

---

## Best Practices

### 1. Granular Tasks

✅ **Good** (2-8 hour tasks):
```json
{
  "id": "auth-jwt-service",
  "title": "Implement JWT token service",
  "estimatedTime": "3h"
}
```

❌ **Bad** (too large):
```json
{
  "id": "implement-everything",
  "title": "Build entire authentication system",
  "estimatedTime": "40h"
}
```

### 2. Clear Dependencies

✅ **Good** (explicit):
```json
{
  "id": "integration-test",
  "dependencies": ["implement-auth", "implement-api", "setup-test-db"]
}
```

❌ **Bad** (implicit):
```json
{
  "id": "integration-test",
  "dependencies": []  // Missing actual dependencies
}
```

### 3. Realistic Estimates

✅ **Good**:
- Include buffer time
- Based on similar past tasks
- Account for complexity

❌ **Bad**:
- Overly optimistic
- No buffer for issues
- Ignoring complexity

### 4. Strategic Parallelization

✅ **Good** (truly independent):
```json
[
  {
    "id": "feature-a",
    "parallelizable": true,
    "description": "Implement feature A in module X"
  },
  {
    "id": "feature-b",
    "parallelizable": true,
    "description": "Implement feature B in module Y"
  }
]
```

❌ **Bad** (false independence):
```json
[
  {
    "id": "edit-file-1",
    "parallelizable": true,
    "description": "Edit user.py lines 1-50"
  },
  {
    "id": "edit-file-2",
    "parallelizable": true,
    "description": "Edit user.py lines 51-100"  // CONFLICT!
  }
]
```

### 5. Descriptive Notes

✅ **Good**:
```json
{
  "status": "completed",
  "notes": "JWT service implemented with HS256 algorithm. Added token refresh endpoint. All 15 tests passing. Coverage: 94%"
}
```

❌ **Bad**:
```json
{
  "status": "completed",
  "notes": "done"
}
```

---

## Examples

### Example 1: Simple Bug Fix
```json
{
  "id": "BUG-2026-01-23-001",
  "created": "2026-01-23T09:00:00Z",
  "tasks": [
    {
      "id": "bug-verify",
      "title": "Verify root cause",
      "description": "Reproduce bug and identify exact cause",
      "status": "completed",
      "dependencies": [],
      "estimatedTime": "30m",
      "parallelizable": false,
      "completedAt": "2026-01-23T09:25:00Z"
    },
    {
      "id": "bug-fix",
      "title": "Implement fix",
      "description": "Fix null pointer in auth validation",
      "status": "completed",
      "dependencies": ["bug-verify"],
      "estimatedTime": "1h",
      "parallelizable": false,
      "completedAt": "2026-01-23T10:30:00Z"
    },
    {
      "id": "bug-test",
      "title": "Write regression test",
      "description": "Test that would have caught this bug",
      "status": "completed",
      "dependencies": ["bug-fix"],
      "estimatedTime": "45m",
      "parallelizable": false,
      "completedAt": "2026-01-23T11:20:00Z"
    }
  ]
}
```

### Example 2: Parallel Feature Development
```json
{
  "id": "CHANGE-2026-01-23-001",
  "created": "2026-01-23T08:00:00Z",
  "tasks": [
    {
      "id": "design",
      "title": "Design architecture",
      "status": "completed",
      "dependencies": [],
      "estimatedTime": "3h",
      "parallelizable": false
    },
    {
      "id": "feature-a",
      "title": "Implement user management",
      "status": "completed",
      "dependencies": ["design"],
      "estimatedTime": "4h",
      "parallelizable": true,
      "notes": "Session A - Completed"
    },
    {
      "id": "feature-b",
      "title": "Implement role management",
      "status": "completed",
      "dependencies": ["design"],
      "estimatedTime": "3h",
      "parallelizable": true,
      "notes": "Session B - Completed"
    },
    {
      "id": "feature-c",
      "title": "Implement permissions",
      "status": "completed",
      "dependencies": ["design"],
      "estimatedTime": "5h",
      "parallelizable": true,
      "notes": "Session C - Completed"
    },
    {
      "id": "integration",
      "title": "Integrate all features",
      "status": "in_progress",
      "dependencies": ["feature-a", "feature-b", "feature-c"],
      "estimatedTime": "2h",
      "parallelizable": false,
      "notes": "Session A - Integrating components"
    }
  ]
}
```

### Example 3: Migration with Phases
```json
{
  "id": "MIG-2026-01-23-HCI",
  "created": "2026-01-23T07:00:00Z",
  "tasks": [
    {
      "id": "mig-phase1-analysis",
      "title": "Analyze legacy codebase",
      "phase": 1,
      "status": "completed",
      "dependencies": [],
      "estimatedTime": "8h",
      "parallelizable": false
    },
    {
      "id": "mig-phase2-setup",
      "title": "Setup modern environment",
      "phase": 2,
      "status": "completed",
      "dependencies": ["mig-phase1-analysis"],
      "estimatedTime": "4h",
      "parallelizable": false
    },
    {
      "id": "mig-phase3-data",
      "title": "Migrate data layer",
      "phase": 3,
      "status": "in_progress",
      "dependencies": ["mig-phase2-setup"],
      "estimatedTime": "12h",
      "parallelizable": false,
      "startedAt": "2026-01-23T15:00:00Z"
    }
  ]
}
```

---

## Integration with MarQed.ai Workflows

### Workflow Scripts

All MarQed.ai workflows use tasks:
```bash
# Bug fix workflow
./workflows/marqed-bugfix.sh --id BUG-001
# Reads: ~/.claude/tasks/BUG-001.json
# Updates: Task statuses as work progresses
# Outputs: Updated PRD.md, WBSO report

# Changes workflow
./workflows/marqed-changes.sh --id CHANGE-001 --parallel 3
# Spawns: 3 parallel sessions
# Coordinates: Through shared task list
# Reports: Progress from all sessions

# Migration workflow
./workflows/marqed-migration.sh --id MIG-001
# Executes: 9 sequential phases
# Tracks: Complex multi-phase progress
# Validates: Each phase completion
```

### Monitoring

Monitor progress in real-time:
```bash
# Live monitoring
./workflows/common/monitor-tasks.sh BUG-001

# Get statistics
./workflows/common/loop-core.sh --stats BUG-001

# Check blockers
./workflows/common/loop-core.sh --blockers BUG-001
```

### Reporting

Generate reports from task data:
```bash
# WBSO R&D report
# Automatically generated on completion
# Location: ~/.marqed/logs/${TASK_ID}/WBSO-REPORT.md

# Contains:
# - All completed tasks
# - Time investment
# - R&D elements
# - Innovation details
```

---

## Advanced Topics

### Custom Task Properties

Add custom fields for specific needs:
```json
{
  "id": "custom-task",
  "customFields": {
    "securityReview": true,
    "performanceTest": true,
    "documentationRequired": true,
    "reviewer": "senior-dev"
  }
}
```

### Task Templates

Create reusable templates:
```json
{
  "templateName": "standard-feature",
  "tasks": [
    {"id": "${PREFIX}-design", "title": "Design ${FEATURE}"},
    {"id": "${PREFIX}-implement", "title": "Implement ${FEATURE}"},
    {"id": "${PREFIX}-test", "title": "Test ${FEATURE}"}
  ]
}
```

### Progress Visualization

Generate progress charts:
```bash
# Extract data
jq -r '.tasks[] | "\(.status)"' tasks.json | sort | uniq -c

# Output:
#   5 completed
#   2 in_progress
#   3 pending
```

---

**Guide Version**: 1.0  
**Last Updated**: January 23, 2026  
**For**: MarQed.ai Workflow System

---

**Master the task system, master the workflow. Happy building!** 🚀✨