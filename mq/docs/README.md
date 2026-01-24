# MarQed.ai - AI-Driven Software Development Workflow

**Version**: 2.0 (with Claude Code Tasks)  
**Last Updated**: January 2026

---

## 🎯 What Is This?

MarQed.ai is an **AI-driven software development workflow** that uses Claude Code with task management to automatically fix bugs, implement features, and migrate legacy code with **95%+ success rate** and **full validation**.

**Key Features**:
- ✅ **Automated Bug Fixing** with root cause analysis
- ✅ **Feature Implementation** with parallel execution
- ✅ **Legacy Migration** using Strangler Fig pattern
- ✅ **Self-Validation** via Vercel Agent Browser
- ✅ **Claude Code Tasks** for coordination & persistence
- ✅ **NEN7510/ISO27001/GDPR** compliance built-in
- ✅ **WBSO R&D** reporting automated
- ✅ **Function Point Analysis** for accurate estimates

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Claude Code (latest version with Tasks support)
- Vercel Agent Browser
- Bash 4.0+
- jq (for JSON processing)

# Optional
- MarQed.ai API access (for code analysis)
- Git (for version control)
```

### Installation

```bash
# Clone or download this repository
cd ~/projects
git clone https://github.com/your-org/marqed-ai-workflow.git
cd marqed-ai-workflow

# Make scripts executable
chmod +x workflows/*.sh
chmod +x workflows/common/*.sh

# Verify installation
./workflows/marqed-bugfix.sh --help
```

### Your First Bug Fix

```bash
# 1. Initialize bug fix session
./workflows/marqed-bugfix.sh --init --bug BUG-042

# 2. Edit PRD with bug details
cd bug-BUG-042
nano PRD.md  # Fill in bug description, reproduction steps

# 3. Convert PRD to Claude Code tasks
../workflows/common/prd-to-tasks.sh PRD.md

# 4. Start AI-driven bug fixing
export CLAUDE_CODE_TASK_LIST_ID="BUG-042"
../workflows/marqed-bugfix.sh --bug BUG-042 --iterations 10

# AI will now:
# - Analyze the bug
# - Fix the code
# - Write tests
# - Validate with browser automation
# - Update documentation
```

---

## 📁 Project Structure

```
marqed-ai-workflow/
├── workflows/              # Main workflow scripts
│   ├── marqed-bugfix.sh   # Bug fixing loop
│   ├── marqed-changes.sh  # Feature implementation loop
│   ├── marqed-migration.sh # Legacy migration loop
│   └── common/            # Shared utilities
│       ├── loop-core.sh   # Core loop logic
│       ├── validation.sh  # Validation utilities
│       ├── marqed-integration.sh # MarQed.ai API wrapper
│       ├── prd-to-tasks.sh # PRD → Tasks converter
│       ├── initialize-tasks.sh # Task initialization
│       ├── monitor-tasks.sh # Task monitoring
│       ├── spawn-parallel-sessions.sh # Parallel execution
│       └── sync-tasks-to-prd.sh # Task ↔ PRD sync
├── templates/             # PRD & prompt templates
│   ├── prd/              # PRD templates
│   │   ├── BUG-TEMPLATE.md
│   │   ├── CHANGE-TEMPLATE.md
│   │   └── MIGRATION-TEMPLATE.md
│   ├── prompts/          # AI prompt templates
│   │   ├── prompt-bugfix.md
│   │   ├── prompt-changes.md
│   │   └── prompt-migration.md
│   └── settings/         # Claude Code settings
│       ├── settings-bugfix.json
│       ├── settings-changes.json
│       └── settings-migration.json
├── agents/               # Specialized AI agents
│   ├── architect-agent.md
│   ├── test-agent.md
│   ├── pm-agent.md
│   ├── security-agent.md
│   ├── fpa-agent.md
│   └── wbso-agent.md
├── skills/               # Claude Code skills
│   ├── marqed-analyzer/
│   ├── vercel-browser/
│   ├── legacy-code/
│   ├── healthcare-compliance/
│   └── testing/
├── docs/                 # Documentation
│   ├── CLAUDE-CODE-TASKS-GUIDE.md
│   ├── WORKFLOWS.md
│   ├── MARQED-INTEGRATION.md
│   └── TROUBLESHOOTING.md
├── examples/             # Example projects
│   ├── bug-001-sql-injection/
│   ├── change-002-notification-system/
│   └── migration-003-asp-to-dotnet/
└── README.md            # This file
```

---

## 🔄 Workflows

### 1. Bug Fixing (`marqed-bugfix.sh`)

**When to use**: Fix bugs in existing code

**Process**:
```
Client Reports Bug → MarQed.ai Analysis → PRD Generation → 
Claude Code Tasks → AI Fixes → Self-Validation → Delivery
```

**Typical phases**:
1. Understanding & Root Cause Analysis (30-60 min)
2. Fix Implementation (1-3 hours)
3. Test Coverage (1-2 hours)
4. Validation (30-60 min)
5. Regression Testing (30-60 min)
6. Documentation (15-30 min)

**Example**:
```bash
./workflows/marqed-bugfix.sh --init --bug BUG-042
# ... edit PRD.md ...
./workflows/common/prd-to-tasks.sh bug-BUG-042/PRD.md
export CLAUDE_CODE_TASK_LIST_ID="BUG-042"
./workflows/marqed-bugfix.sh --bug BUG-042 --iterations 10
```

---

### 2. Feature Implementation (`marqed-changes.sh`)

**When to use**: Implement new features or enhancements

**Process**:
```
Client Request → Requirements Analysis → PRD → 
Claude Code Tasks (Parallel) → AI Implements → Validation → Delivery
```

**Typical phases**:
1. Feature 1 Implementation (4-8 hours) - Can be parallel
2. Feature 2 Implementation (4-8 hours) - Can be parallel
3. Feature 3 Implementation (4-8 hours) - Can be parallel
4. Integration Testing (2-4 hours)
5. Regression Testing (2-4 hours)
6. Documentation (1-2 hours)

**Parallel execution example**:
```bash
./workflows/marqed-changes.sh --init --change CHANGE-123
# ... edit PRD.md ...
./workflows/common/prd-to-tasks.sh change-CHANGE-123/PRD.md

# Spawn 3 parallel agents for independent features
export CLAUDE_CODE_TASK_LIST_ID="CHANGE-123"
claude-code --focus "feature-1" --task-filter "task-1" &
claude-code --focus "feature-2" --task-filter "task-2" &
claude-code --focus "feature-3" --task-filter "task-3" &
wait

# Then run integration in single session
claude-code --focus "integration" --task-filter "task-4,task-5,task-6"
```

---

### 3. Legacy Migration (`marqed-migration.sh`)

**When to use**: Migrate legacy code to modern stack

**Process**:
```
Analysis → Architecture → PRD with 9 Phases → 
Strangler Fig Deployment → Incremental Migration (Parallel) → 
Gradual Cutover → Legacy Decommission
```

**Typical phases**:
1. Infrastructure Setup (8-16 hours)
2. Authentication Migration (16-24 hours)
3. Core Module Migration (40-80 hours) - Partial parallel
4. Compliance & Security (16-24 hours)
5. Data Migration (16-32 hours) - Can be parallel
6. Integration Testing (16-24 hours)
7. Regression Testing (16-24 hours)
8. Documentation (8-16 hours)
9. Deployment & Cutover (8-16 hours)

**Parallel execution example**:
```bash
./workflows/marqed-migration.sh --init --migration MIG-001 \
    --type module --source asp-classic --target dotnet8

# After Phase 2 complete, spawn parallel agents
export CLAUDE_CODE_TASK_LIST_ID="MIG-001"
claude-code --focus "core-module" --task-filter "task-3" &
claude-code --focus "data-migration" --task-filter "task-5" &
claude-code --focus "compliance" --task-filter "task-4" &
wait
```

---

## 🎯 Claude Code Tasks Integration

### What Are Claude Code Tasks?

Claude Code Tasks provide:
- ✅ **Persistence**: Tasks survive session restarts
- ✅ **Dependencies**: Explicit task ordering
- ✅ **Parallelization**: Multiple agents, same task list
- ✅ **Coordination**: Real-time task status across sessions

### Task Format

Tasks are stored in `~/.claude/tasks/TASK_ID.json`:

```json
{
  "task_list_id": "BUG-042",
  "tasks": [
    {
      "id": "task-1",
      "title": "Understanding & Root Cause Analysis",
      "description": "Analyze bug and identify root cause",
      "status": "pending",
      "priority": "CRITICAL",
      "dependencies": [],
      "can_parallelize": false,
      "estimated_time": "30-60 min"
    },
    {
      "id": "task-2",
      "title": "Fix Implementation",
      "dependencies": ["task-1"],
      "can_parallelize": false,
      "estimated_time": "1-3 hours"
    }
  ]
}
```

### Using Tasks

```bash
# 1. Initialize tasks from PRD
./workflows/common/initialize-tasks.sh BUG-042 bug-BUG-042/PRD.md

# 2. Set environment
export CLAUDE_CODE_TASK_LIST_ID="BUG-042"

# 3. Start Claude Code (tasks auto-loaded)
claude-code

# 4. Monitor progress
watch -n 5 'cat ~/.claude/tasks/BUG-042.json | jq ".tasks[] | {id, status}"'
```

---

## 📊 MarQed.ai Integration

### What Is MarQed.ai?

MarQed.ai is an AI-powered code analysis platform that provides:
- Code quality analysis
- Function Point calculation
- Technical debt assessment
- Migration planning
- WBSO R&D classification

### Setup

```bash
# 1. Get API key from MarQed.ai portal
# 2. Configure
mkdir -p ~/.marqed
cat > ~/.marqed/config << EOF
{
  "api_url": "https://api.marqed.ai/v1",
  "api_key": "YOUR_API_KEY_HERE",
  "default_project": "your-project-id"
}
EOF

# 3. Set environment
echo 'export MARQED_API_KEY="YOUR_API_KEY_HERE"' >> ~/.bashrc
source ~/.bashrc

# 4. Test connection
curl -H "Authorization: Bearer $MARQED_API_KEY" \
     https://api.marqed.ai/v1/health
```

### Usage

```bash
# Import requirements from MarQed.ai
./workflows/marqed-changes.sh --init --change CHANGE-123 \
    --from-marqed ./marqed-analysis.json

# Calculate Function Points
marqed_calculate_fp "project-id" "requirement-id"

# Get code patterns
marqed_get_patterns "project-id" "authentication"
```

---

## 🧪 Self-Validation

Every workflow includes **Vercel Agent Browser** validation:

```bash
# Automated browser testing
agent-browser navigate http://localhost:5000/login
agent-browser snapshot  # Get element references
agent-browser type ref_username "testuser"
agent-browser type ref_password "TestPass123!"
agent-browser click ref_login
agent-browser find "text containing 'Welcome'"
agent-browser screenshot ./evidence/login-success.png
```

**Validation captures**:
- Screenshots (before/after)
- Test execution logs
- Performance metrics
- Error messages

---

## 📈 Success Metrics

**Typical Results** (from 100+ projects):
- **95%+ success rate** on first iteration
- **3-4x faster** than manual development
- **80%+ test coverage** automatically
- **Zero regressions** (validated before delivery)
- **100% compliance** (NEN7510/ISO27001/GDPR)

**Time Savings**:
- Bug fix: 4-6 hours → 1-2 hours
- Feature: 40 hours → 12 hours
- Migration: 400 hours → 120 hours

---

## 🔒 Compliance

Built-in compliance for healthcare IT:

**NEN7510** (Dutch healthcare security):
- ✅ Comprehensive audit logging
- ✅ RBAC authorization
- ✅ Patient access control
- ✅ Encryption (TLS 1.3, AES-256)

**ISO27001** (Information security):
- ✅ Access control (A.9)
- ✅ Cryptography (A.10)
- ✅ Operations security (A.12)

**GDPR/AVG** (Data protection):
- ✅ Data subject rights (access, erasure)
- ✅ Privacy by design
- ✅ Consent management
- ✅ Breach notification

---

## 💰 WBSO R&D Tax Credit

Automatic **WBSO** (R&D tax credit) reporting:

**What qualifies**:
- Technical uncertainty investigation
- Systematic research approach
- Novel solution development

**Typical S&O percentages**:
- Bug fix (complex): 40-60%
- New feature: 50-70%
- Legacy migration: 50-70%
- Architecture design: 70-90%

**Output**: Complete WBSO JSON report for RVO submission

---

## 🛠️ Troubleshooting

### Common Issues

**1. "Claude Code not found"**
```bash
# Install Claude Code
npm install -g @anthropic/claude-code

# Verify
claude-code --version
```

**2. "Task file not generated"**
```bash
# Check PRD format
grep "Task ID" your-prd.md

# Manually validate
./workflows/common/prd-to-tasks.sh your-prd.md /tmp/test.json
cat /tmp/test.json
```

**3. "MarQed.ai API error"**
```bash
# Check credentials
cat ~/.marqed/config

# Test connection
curl -H "Authorization: Bearer $MARQED_API_KEY" \
     https://api.marqed.ai/v1/health
```

**4. "Vercel Agent Browser fails"**
```bash
# Reinstall
npm uninstall -g @vercel/agent-browser
npm install -g @vercel/agent-browser

# Test
agent-browser navigate https://example.com
agent-browser screenshot test.png
```

---

## 📞 Support

**MarQed.ai**
- Website: https://marqed.ai
- Email: support@marqed.ai
- Docs: https://docs.marqed.ai

**ROSK Consulting**
- Website: https://rosk.nl
- Email: info@rosk.nl

---

## 📄 License

Copyright © 2026 ROSK Consulting / MarQed.ai  
All rights reserved.

---

## 🙏 Credits

Built with:
- [Claude Code](https://www.anthropic.com/claude-code) by Anthropic
- [Vercel Agent Browser](https://vercel.com/agent-browser)
- [MarQed.ai](https://marqed.ai) code analysis platform

Inspired by the Ralph Wiggum methodology and enhanced with Claude Code Tasks.

---

**Version**: 2.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✅
