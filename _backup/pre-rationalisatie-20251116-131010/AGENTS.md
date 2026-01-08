# 🤖 AGENTS - AI Agent System Reference

**Doel**: Complete agent system documentation op één plek
**Doelgroep**: Developers working with agents
**Last Updated**: 2025-11-16

---

## 🎯 Quick Overview

**10 Specialized AI Agents** - 100% Local Execution (Ollama)
**9 Work Type Workflows** - Intelligent routing
**4 Scrum Ceremonies** - Automated
**16 SuperClaude Commands** - Domain expertise
**Quality Gates** - Integrated validation

---

## 📋 The 10 Agents

### Core Agents (8)

#### 1. Felix - Feature Architect
- **Role**: Architecture & feature design
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: System design, API design, work breakdown
- **Workflows**: NEW_FEATURE, PROJECT_DEFINITION

#### 2. Marcus - Maintenance Specialist  
- **Role**: Code maintenance & tech debt
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Refactoring, dependency updates, code health
- **Workflows**: MAINTENANCE

#### 3. Quinn - Quality Inspector
- **Role**: Quality assurance & security
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: Code review, security audits, quality gates
- **Workflows**: QUALITY_AUDIT, QUALITY_IMPROVEMENT

#### 4. Betty - Bug Hunter
- **Role**: Bug investigation & fixing
- **LLM**: codellama:latest (local)
- **Specialties**: Debugging, root cause analysis, error handling
- **Workflows**: BUG

#### 5. Eliza - Estimation Engine
- **Role**: Effort estimation & complexity analysis
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: Function points, story points, ML-based estimation
- **Workflows**: All (provides estimates)

#### 6. Tessa - Test Engineer
- **Role**: Test automation & coverage
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Unit tests, E2E tests, test strategy
- **Workflows**: TESTING, all workflows (provides test coverage)

#### 7. Miguel - Migration Architect
- **Role**: Migration & platform upgrades
- **LLM**: qwen2.5-coder:7b (local)
- **Specialties**: Tech stack migrations, data migrations
- **Workflows**: MIGRATION

#### 8. Diana - Documentation Writer
- **Role**: Technical documentation
- **LLM**: mistral:latest (local)
- **Specialties**: API docs, architecture docs, user guides
- **Workflows**: All (provides documentation)

### Management Agents (2)

#### 9. Peter - Product Owner
- **Role**: Requirements & product vision
- **LLM**: deepseek-r1:latest (local)
- **Specialties**: User stories, business analysis, prioritization
- **Workflows**: PROJECT_DEFINITION

#### 10. Paul - Project Lead
- **Role**: Project planning & coordination
- **LLM**: qwen2.5:7b (local)
- **Specialties**: Resource allocation, sprint planning, risk management
- **Workflows**: PROJECT_DEFINITION

---

## 🔄 The 9 Work Type Workflows

### 1. NEW_FEATURE (Spec-Kit Pipeline)
**Agents**: Peter → Felix → Diana  
**Process**: Constitution → Specification → Tasks  
**Output**: Complete project definition with epics/features/stories

### 2. MAINTENANCE (6-Stage Automation)
**Agents**: Marcus → Quinn → Tessa → Eliza  
**Process**: Audit → Plan → Execute → Test → Document → Deploy  
**Output**: Updated dependencies, refactored code, technical debt reduction

### 3. BUG (5-Stage Bug Fixing)
**Agents**: Betty → Tessa → Diana  
**Process**: Reproduce → Diagnose → Fix → Test → Document  
**Output**: Bug fix with regression tests

### 4. QUALITY_AUDIT (SuperClaude Integration)
**Agents**: Quinn → Felix → Marcus  
**Process**: Scan → Analyze → Recommend → Prioritize  
**Output**: Risk-prioritized remediation plan

### 5. ENHANCEMENT
**Agents**: Felix → Tessa → Diana  
**Process**: Design → Implement → Test → Document  
**Output**: Feature enhancement

### 6. MIGRATION (5-Stage Pipeline)
**Agents**: Miguel → Felix → Tessa → Diana  
**Process**: Assess → Plan → Execute → Validate → Cutover  
**Output**: Migrated codebase

### 7. QUALITY_IMPROVEMENT
**Agents**: Quinn → Marcus → Tessa  
**Process**: Audit → Refactor → Test  
**Output**: Improved code quality

### 8. TESTING
**Agents**: Tessa → Quinn → Diana  
**Process**: Strategy → Execute → Report  
**Output**: Comprehensive test suite

### 9. PROJECT_DEFINITION (Complete Project Setup)
**Agents**: Peter → Felix → Paul → Diana  
**Process**: Vision → Architecture → Planning → Documentation  
**Output**: Complete project charter with folder structure

---

## 🎭 Scrum Ceremonies (4 Automated)

### 1. Daily Standup
**Frequency**: On-demand or scheduled  
**Participants**: All active agents  
**Output**: Status reports, blockers, peer assistance requests

### 2. Sprint Planning
**Frequency**: Start of sprint (2 weeks)  
**Process**: Backlog prioritization → Capacity planning → Story selection  
**Output**: Sprint backlog with risk assessment

### 3. Sprint Review
**Frequency**: End of sprint  
**Process**: Demo preparation → Stakeholder feedback → Acceptance validation  
**Output**: Accepted work + backlog refinements

### 4. Sprint Retrospective
**Frequency**: After sprint review  
**Process**: Feedback collection → Team health assessment → Action items  
**Output**: Process improvements + learning outcomes

---

## 🎯 Quality Gates Integration

**7 Gate Types**: Architecture, Code Quality, Test Coverage, Security, Documentation, Performance, Accessibility  
**42 Validation Rules**: Distributed across 5 validators  
**Retry Mechanism**: 3 attempts with exponential backoff  
**Peer Assistance**: Agent-to-agent help (confidence > 0.6)  
**Escalation**: Multi-channel notifications for critical issues

---

## ⚡ The 16 SuperClaude Slash Commands

### Core 4 Commands (Detailed)

#### /architect 🏗️
**Purpose**: Architecture reviews & design pattern recommendations  
**Output**: Architecture score, patterns detected, recommendations  
**Use When**: Architecture changes, design reviews

#### /reviewer 👀
**Purpose**: PR reviews & code quality audits  
**Output**: Quality score, code smells, refactoring suggestions  
**Use When**: Pull request reviews, code quality checks

#### /optimizer ⚡
**Purpose**: Performance audits & bottleneck detection  
**Output**: Performance score, bottlenecks, optimization strategies  
**Use When**: Performance issues, slow queries

#### /debugger 🐛
**Purpose**: Bug investigation & root cause analysis  
**Output**: Robustness score, potential bugs, fix recommendations  
**Use When**: Debugging complex issues, error analysis

### Additional 12 Commands

- **/tester** 🧪 - Test generation & strategy
- **/documenter** 📚 - Documentation generation
- **/security** 🔒 - Security audit (OWASP Top 10)
- **/refactor** 🔄 - Refactoring suggestions
- **/api-designer** 🔌 - API design review
- **/database** 🗄️ - Database optimization
- **/frontend** 🎨 - Frontend review (UI/UX)
- **/backend** ⚙️ - Backend analysis
- **/devops** 🚀 - DevOps review (CI/CD)
- **/accessibility** ♿ - A11y audit (WCAG)
- **/performance** ⚡ - Performance audit
- **/migration** 📦 - Migration strategy

---

## 🔧 LLM Configuration (100% Local)

**All models via Ollama** - No cloud dependencies, complete privacy

| Model | Size | Agents | Specialty |
|-------|------|--------|-----------|
| qwen2.5-coder:7b | 4.7 GB | Felix, Marcus, Tessa, Miguel | Code generation & refactoring |
| deepseek-r1:latest | 5.2 GB | Quinn, Eliza, Peter | Reasoning & analysis |
| codellama:latest | 3.8 GB | Betty | Debugging |
| mistral:latest | 4.4 GB | Diana | Documentation |
| qwen2.5:7b | 4.7 GB | Paul | Planning |

**Benefits**:
- ✅ Complete privacy (no data leaves your machine)
- ✅ No API costs
- ✅ Offline capability
- ✅ Consistent performance

---

## 🔄 Retry + Peer Assistance System

### Retry Mechanism
- **Max Attempts**: 3
- **Backoff**: Exponential (2s → 4s → 8s)
- **Enhanced Feedback**: Quality gate recommendations + slash command insights
- **Blocking Detection**: Automatic escalation after max retries

### Peer Assistance
- **Trigger**: Agent requests help during standup
- **Selection**: Confidence scoring (>0.6 required)
- **Assistance Types**: TIP, RESOURCE, TAKEOVER, PAIR, REVIEW, CONSULT
- **Expertise Mapping**: Each agent has 3-5 specialties

### Human Escalation
- **Channels**: EMAIL, SLACK, WEBHOOK, LOG
- **Priority Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Immediate Escalation**: BUG & QUALITY_AUDIT work types
- **Auto-Resolution**: Self-correcting errors

---

## 📊 Agent Collaboration Patterns

### Sequential Pattern
**Use When**: Each step depends on previous output  
**Example**: NEW_FEATURE (Peter → Felix → Diana)  
**Benefit**: Clear dependencies, ordered execution

### Parallel Pattern
**Use When**: Independent tasks can run simultaneously  
**Example**: QUALITY_AUDIT (multiple code scans)  
**Benefit**: Faster execution

### Hybrid Pattern (Most Common)
**Use When**: Mix of dependent and independent tasks  
**Example**: MAINTENANCE (audit parallel, fixes sequential)  
**Benefit**: Optimal speed + correct dependencies

---

## 🚀 Quick Start

### Run a Workflow

```bash
# Via API
curl -X POST http://localhost:8000/api/workflows/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "work_type": "NEW_FEATURE",
    "description": "Build user authentication system",
    "enable_retry": true,
    "enable_peer_help": true
  }'
```

### Check Agent Status

```bash
curl http://localhost:8000/api/workflows/agents
```

### Get Statistics

```bash
curl http://localhost:8000/api/workflows/statistics
```

---

## 🔍 Troubleshooting

### Agent Not Responding
1. Check Ollama is running: `ollama list`
2. Verify model is pulled: `ollama pull qwen2.5-coder:7b`
3. Check agent service logs

### Workflow Timeout
- Default: 30 minutes (soft timeout with warnings)
- User-controlled execution (no automatic kills)
- Check work type complexity

### Quality Gate Failures
- Review gate configuration in ARCHITECTURE.md
- Check which validation rule failed
- Use slash commands for enhanced feedback

---

## 📚 Related Documentation

- **Full Agent Specifications**: `backend/agents/AGENT_SPECIFICATIONS.md`
- **Integration Guide**: `backend/agents/INTEGRATION_GUIDE.md`  
- **LLM Configuration**: `backend/agents/LLM_CONFIGURATION.md`
- **Architecture Details**: `ARCHITECTURE.md`
- **Planning & Roadmap**: `ROADMAP.md`

---

**Last Updated**: 2025-11-16  
**Version**: 2.0 (Consolidated)  
**Status**: ✅ Complete - All 10 agents operational
