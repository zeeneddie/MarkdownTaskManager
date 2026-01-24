# Context Handover Document - MarQed.ai Workflow System

**Date**: January 23, 2026  
**Session**: Token Budget 67% gebruikt (128K/190K)  
**Status**: 5 van 22 kritieke files klaar

---

## 🎯 Project Overview

**What we're building**: Complete AI-driven software development workflow system for MarQed.ai (rebranded from "Ralph Wiggum")

**Key Changes Made**:
1. ✅ Integrated **Claude Code Tasks** (persistence, dependencies, parallelization)
2. ✅ Rebranded **Ralph → MarQed.ai** throughout all naming
3. ✅ Upgraded all templates with task metadata

---

## ✅ Files COMPLETED in This Session

### Templates (2 files)
1. ✅ **MIGRATION-TEMPLATE-v2.md** (9 phases, ~256h scope, full task metadata)
2. ✅ **CHANGE-TEMPLATE-v2.md** (6 phases, parallel-ready, task metadata)

### Scripts (2 files)
3. ✅ **prd-to-tasks.sh** (PRD → Claude Code tasks JSON converter)
4. ✅ **initialize-tasks.sh** (Task initialization wrapper)

### Documentation (1 file)
5. ✅ **README.md** (Complete project overview, quick start, all workflows)

**All 5 files are in**: `/mnt/user-data/outputs/`

---

## ⏳ Files REMAINING (17 files)

### Priority P0 - CRITICAL (complete eerst deze)

#### Templates (1 file)
6. ⏳ **BUG-TEMPLATE-v2.md**
   - ALREADY DONE but needs final review
   - Located at: `/mnt/user-data/outputs/BUG-TEMPLATE-FINAL.md`
   - Action: Rename to BUG-TEMPLATE-v2.md and ensure consistency

#### Prompts (2 files)
7. ⏳ **prompt-bugfix.md**
   - Location: `templates/prompts/prompt-bugfix.md`
   - Add: Claude Code task instructions
   - Add: How to update task status
   - Add: Dependency awareness

8. ⏳ **prompt-changes.md**
   - Location: `templates/prompts/prompt-changes.md`
   - Add: Task management instructions
   - Add: Parallel execution guidance
   - Add: Feature coordination

---

### Priority P1 - HIGH (daarna deze)

#### Workflows (3 files)
9. ⏳ **marqed-bugfix.sh**
   - Location: `workflows/marqed-bugfix.sh`
   - Base: Existing ralph-bugfix.sh
   - Changes:
     - Rename ralph → marqed throughout
     - Add: Task initialization call
     - Add: `export CLAUDE_CODE_TASK_LIST_ID`
     - Add: Claude Code session start with tasks

10. ⏳ **marqed-changes.sh**
    - Location: `workflows/marqed-changes.sh`
    - Base: Existing ralph-changes.sh
    - Changes:
      - Rename ralph → marqed
      - Add: Multi-session spawning for parallel features
      - Add: Task progress monitoring

11. ⏳ **marqed-migration.sh**
    - Location: `workflows/marqed-migration.sh`
    - Status: ALREADY EXISTS in outputs (ralph-migration.sh)
    - Action: Rename ralph → marqed throughout

#### Common Scripts (4 files)
12. ⏳ **loop-core.sh**
    - Location: `workflows/common/loop-core.sh`
    - Add: `check_tasks_complete()` function
    - Add: `sync_tasks_to_prd()` function
    - Update: Main loop to respect task status

13. ⏳ **validation.sh**
    - Location: `workflows/common/validation.sh`
    - Add: `validate_task_complete()` function
    - Add: Task status update on validation pass

14. ⏳ **monitor-tasks.sh**
    - Location: `workflows/common/monitor-tasks.sh`
    - New file
    - Function: Real-time task progress monitoring
    - Watch ~/.claude/tasks/${ID}.json and display

15. ⏳ **spawn-parallel-sessions.sh**
    - Location: `workflows/common/spawn-parallel-sessions.sh`
    - New file
    - Function: Spawn multiple Claude Code sessions
    - Share same CLAUDE_CODE_TASK_LIST_ID

16. ⏳ **sync-tasks-to-prd.sh**
    - Location: `workflows/common/sync-tasks-to-prd.sh`
    - New file
    - Function: Update PRD.md when tasks complete
    - Mark phases as `passes: true`

---

### Priority P2 - MEDIUM (als P0+P1 klaar)

#### Agents (3 files)
17. ⏳ **architect-agent.md**
    - Add: Task breakdown guidance
    - Add: Dependency planning
    - Add: Parallelization identification

18. ⏳ **test-agent.md**
    - Add: Parallel test coordination
    - Add: Task status updates

19. ⏳ **pm-agent.md**
    - Add: Task progress tracking
    - Add: Bottleneck identification

#### Settings (3 files)
20. ⏳ **settings-bugfix.json**
    - Add: `claudeCodeTasks.enabled: true`
    - Add: `taskListPrefix: "BUG-"`

21. ⏳ **settings-changes.json**
    - Add: Same as bugfix

22. ⏳ **settings-migration.json**
    - Add: Same as bugfix

---

### Priority P3 - LOW (polish, kan later)

#### Documentation (2 files)
23. ⏳ **CLAUDE-CODE-TASKS-GUIDE.md**
    - Complete guide on Claude Code tasks
    - How MarQed.ai uses them
    - Troubleshooting

24. ⏳ **WORKFLOWS.md**
    - Update with task integration
    - Add parallel execution examples

---

## 📝 Template for Each File

### For Prompts (prompt-bugfix.md, prompt-changes.md)

**Structure to follow**:
```markdown
# [Workflow] Prompt - MarQed.ai Methodology

You are an expert [role] working on [workflow type].

## Claude Code Tasks Integration

Before starting, you have access to a task list:
- Tasks are in ~/.claude/tasks/TASK_ID.json
- Respect dependencies
- Update status as you progress
- Can parallelize when marked

## Step-by-Step Process

### Step 1: Load Task Context
[Instructions for reading task list]

### Step 2: Execute Current Task
[Detailed instructions]

### Step 3: Update Task Status
[How to mark task complete]

[Rest of original prompt content with task awareness]
```

---

### For Workflows (marqed-*.sh)

**Pattern to follow**:
```bash
#!/bin/bash
# marqed-[type].sh - [Description]
# Part of MarQed.ai AI-driven development workflow

# Initialize tasks
source workflows/common/initialize-tasks.sh
initialize_tasks_from_prd "$ID" "path/PRD.md"

# Set environment
export CLAUDE_CODE_TASK_LIST_ID="$ID"

# Start Claude Code with tasks
claude-code --task-list "$ID" \
            --context "path" \
            --prompt "$(cat prompt.md)"
```

**Key changes from ralph-*.sh**:
1. Replace `ralph` → `marqed` in all:
   - Function names
   - Comments
   - Echo messages
   - File references
2. Add task initialization
3. Add CLAUDE_CODE_TASK_LIST_ID export
4. Update Claude Code invocation

---

### For Common Scripts

**monitor-tasks.sh structure**:
```bash
#!/bin/bash
# Monitor Claude Code task progress in real-time

TASK_ID="$1"
TASKS_FILE=~/.claude/tasks/${TASK_ID}.json

watch -n 2 "cat $TASKS_FILE | jq '.tasks[] | {id, title, status}'"
```

**spawn-parallel-sessions.sh structure**:
```bash
#!/bin/bash
# Spawn parallel Claude Code sessions

TASK_ID="$1"
shift
FILTERS=("$@")

for filter in "${FILTERS[@]}"; do
    CLAUDE_CODE_TASK_LIST_ID="$TASK_ID" \
        claude-code --task-filter "$filter" &
done

wait
```

**sync-tasks-to-prd.sh structure**:
```bash
#!/bin/bash
# Sync task status → PRD.md

TASK_ID="$1"
PRD_FILE="$2"

# Read task statuses
# For each completed task, find matching phase in PRD
# Update "Passes: false" → "Passes: true"
```

---

### For Settings JSON

**Template**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/claude"]
    }
  },
  "claudeCodeTasks": {
    "enabled": true,
    "taskListPrefix": "[BUG|CHANGE|MIG]-"
  },
  "customInstructions": "You are working on [type] using MarQed.ai methodology...",
  "name": "MarQed [Type]",
  "temperature": 0.3,
  "maxTokens": 8000
}
```

---

### For Agent Files

**Add to each agent.md**:
```markdown
## Claude Code Tasks Responsibilities

### As [Agent Role], you handle:
- Task breakdown for [domain]
- Dependency identification
- Parallelization opportunities
- Progress tracking

### When Working With Tasks:
1. Review entire task list first
2. Identify your responsibilities
3. Update task status as you complete work
4. Coordinate with other agents via shared task list
```

---

## 🎨 Naming Conventions

**Critical**: Replace ALL instances of "Ralph" with "MarQed.ai"

### In Scripts
```bash
# OLD
ralph-bugfix.sh
ralph_bugfix_loop()
RALPH_STATE_DIR

# NEW
marqed-bugfix.sh
marqed_bugfix_loop()
MARQED_STATE_DIR
```

### In Comments
```bash
# OLD
# Ralph Wiggum methodology
# Part of Ralph loop

# NEW  
# MarQed.ai methodology
# Part of MarQed.ai loop
```

### In Documentation
```markdown
# OLD
Ralph Wiggum is an AI-driven...
The Ralph loop continues...

# NEW
MarQed.ai is an AI-driven...
The MarQed.ai loop continues...
```

### Exceptions (keep as-is)
- Historical references: "Inspired by Ralph Wiggum methodology"
- Credit section: Can mention Ralph as predecessor
- Git history: Don't rewrite history

---

## 🔍 Quality Checklist

For each file you create, verify:

### Bash Scripts
- [ ] Shebang: `#!/bin/bash`
- [ ] `set -e` for error handling
- [ ] Usage function with examples
- [ ] All variables quoted: `"$variable"`
- [ ] Comments explain WHY not WHAT
- [ ] Error messages to stderr: `>&2`
- [ ] Success messages clear and actionable
- [ ] No hardcoded paths (use variables)

### Markdown Files
- [ ] Clear hierarchy (# ## ###)
- [ ] Code blocks have language tags
- [ ] Examples are complete and runnable
- [ ] Cross-references use relative paths
- [ ] No broken links
- [ ] Consistent tone (professional but friendly)

### JSON Files
- [ ] Valid JSON (test with `jq`)
- [ ] No trailing commas
- [ ] Proper escaping of strings
- [ ] Consistent indentation (2 spaces)

---

## 📊 Progress Tracking

### Session 1 (This Session)
**Token Usage**: 67% (128K/190K)
**Files Completed**: 5/22 (23%)
**Estimated Remaining**: 3-4 more sessions

### What to Do Next Session

**Start with P0 (Critical)**:
1. Review BUG-TEMPLATE-FINAL.md → rename to v2
2. Create prompt-bugfix.md
3. Create prompt-changes.md

**Then P1 (High)**:
4. Create marqed-bugfix.sh
5. Create marqed-changes.sh
6. Update marqed-migration.sh (rename from ralph)
7. Create loop-core.sh updates
8. Create validation.sh updates
9. Create monitor-tasks.sh (new)
10. Create spawn-parallel-sessions.sh (new)
11. Create sync-tasks-to-prd.sh (new)

**Batch Creation Strategy**:
You can create multiple small files per prompt efficiently:
- Settings JSON: All 3 in one go (they're tiny)
- Agent updates: All 3 in one go (just additions)
- Simple scripts: 2-3 per prompt

---

## 🎯 Success Criteria

Session complete when:
- [ ] All 22 files created and downloadable
- [ ] All naming changed ralph → marqed
- [ ] All scripts executable (`chmod +x`)
- [ ] All JSON files valid
- [ ] All markdown properly formatted
- [ ] README.md updated with final status
- [ ] CHANGELOG.md created documenting changes

---

## 💾 File Locations

**Current outputs** (this session):
- `/mnt/user-data/outputs/MIGRATION-TEMPLATE-v2.md`
- `/mnt/user-data/outputs/CHANGE-TEMPLATE-v2.md`
- `/mnt/user-data/outputs/prd-to-tasks.sh`
- `/mnt/user-data/outputs/initialize-tasks.sh`
- `/mnt/user-data/outputs/README.md`
- `/mnt/user-data/outputs/BUG-TEMPLATE-FINAL.md` (needs rename)

**Previous outputs** (still available):
- Check `/mnt/user-data/outputs/` for other files from earlier

---

## 📞 Contact & Questions

If unclear about anything:
1. Check existing completed files for patterns
2. Reference this handover doc
3. Ask Eddie for clarification on business logic
4. Use README.md as source of truth for structure

---

## 🚀 Quick Start for Next Session

**Opening prompt suggestion**:
```
Hi Claude! I need you to continue building the MarQed.ai workflow system.

Please read /mnt/user-data/outputs/CONTEXT-HANDOVER.md first - it has 
complete context on what we're building and what's left to do.

Then let's start with Priority P0 files:
1. prompt-bugfix.md
2. prompt-changes.md

Use the template and patterns from that handover doc.
```

---

**Good luck with the next session! 🎉**

---

**Document Version**: 1.0  
**Created**: January 23, 2026  
**For**: Claude (Next Session)  
**By**: Claude (Current Session) + Eddie
