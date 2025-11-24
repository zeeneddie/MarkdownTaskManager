# AI Assistants Integration

> **[Back to README](../README.md)**

This system is designed to work with AI assistants to achieve **complete traceability** of work done.

---

## Principle

AI assistants (Claude, ChatGPT, Copilot, Gemini, etc.) can:
1. Create tasks with strict format in `kanban.md`
2. Break down complex tasks into subtasks
3. Update progress in real time
4. Document complete result in `**Notes**:`
5. Reference tasks in Git commits (`TASK-XXX`)
6. Archive on demand only (not automatically)

---

## Configuration

Each AI has its own configuration file that should reference `AI_WORKFLOW.md`:

| AI Assistant | Configuration File | Location |
|--------------|-------------------|----------|
| **Claude** (Anthropic) | `CLAUDE.md` | Project root |
| **GitHub Copilot** (Microsoft) | `copilot-instructions.md` | `.github/` |
| **OpenAI CLI** (GPT-4, GPT-3.5) | `OPENAI_CLI.md` | Project root |
| **ChatGPT** (OpenAI Web/Desktop) | `CHATGPT.md` or Custom GPT | Root or Web |
| **Gemini** (Google) | `GEMINI.md` or `instructions.md` | Root or `.gemini/` |
| **Qwen** (Alibaba) | `QWEN.md` or `.qwenrc` | Project root |
| **Codeium / Windsurf** | `instructions.md` | `.windsurf/` or `.codeium/` |

**Available templates:**
- `CLAUDE.md.exemple`
- `COPILOT.md.exemple`
- `CHATGPT.md.exemple`
- `GEMINI.md.exemple`
- `QWEN.md.exemple`
- `CODEIUM.md.exemple`
- `OPENAI_CLI.md.exemple`

---

## Quick Installation

### Step 1: Copy base files

```bash
# Required files
cp AI_WORKFLOW.md your-project/
cp kanban.md your-project/
cp archive.md your-project/
```

### Step 2: Configure your preferred AI

#### Claude

```bash
cp CLAUDE.md.exemple your-project/CLAUDE.md
```

**For Claude Code (CLI)**: A dedicated skill is available!
```bash
# Copy the skill directory (metadata lives in SKILL.md)
cp -R .claude/skills/markdown-task-manager ~/.claude/skills/
# Restart Claude Code to activate the skill
```

Claude Code reads the `SKILL.md` metadata inside this directory, which is why the whole folder must be copied. The `markdown-task-manager` skill enables Claude Code to automatically manage your tasks with the required strict format. Once installed globally, it's available across all your projects.

**Using the Claude Code skill:**
Once the skill is installed and Claude Code is restarted, the skill will automatically detect projects containing `kanban.md` and `archive.md`. You can simply ask:
- "Create a task to implement authentication"
- "Update TASK-007 with results"
- "List all tasks in progress"
- "Archive completed tasks"

Claude Code will automatically follow the strict format and manage your tasks correctly.

#### GitHub Copilot

```bash
mkdir -p your-project/.github
cp COPILOT.md.exemple your-project/.github/copilot-instructions.md
```

#### ChatGPT

```bash
cp CHATGPT.md.exemple your-project/CHATGPT.md
```

#### Gemini

```bash
mkdir -p your-project/.gemini
cp GEMINI.md.exemple your-project/.gemini/instructions.md
```

#### Windsurf / Codeium

```bash
mkdir -p your-project/.windsurf
cp CODEIUM.md.exemple your-project/.windsurf/instructions.md
```

#### OpenAI CLI

```bash
cp OPENAI_CLI.md.exemple your-project/OPENAI_CLI.md
```

#### Qwen

```bash
cp QWEN.md.exemple your-project/QWEN.md
```

### Step 3: Final structure

```bash
your-project/
├── AI_WORKFLOW.md              # <- General guidelines for all AIs
├── CLAUDE.md                   # <- Claude configuration (optional)
├── .github/
│   └── copilot-instructions.md # <- Copilot configuration (optional)
├── .gemini/
│   └── instructions.md         # <- Gemini configuration (optional)
├── .windsurf/
│   └── instructions.md         # <- Windsurf configuration (optional)
├── kanban.md                   # <- Active tasks
├── archive.md                  # <- Archived tasks
└── src/
```

---

## First Use

**For Claude:**
```
"Read CLAUDE.md and use the task system"
```

**For GitHub Copilot:**
```
@workspace Read AI_WORKFLOW.md and create a task for [feature]
```

**For ChatGPT:**
1. Upload `CHATGPT.md` and `AI_WORKFLOW.md`
2. Say: `"Read these files and use the task system"`

**For Gemini:**
```
@workspace Read AI_WORKFLOW.md and plan [feature]
```

**For Windsurf / Codeium:**
```
Read AI_WORKFLOW.md and create TASK-001 for [feature]
```

**For OpenAI CLI:**
```bash
openai --system-file OPENAI_CLI.md "Read AI_WORKFLOW.md and create a task for [feature]"
```

**For Qwen:**
```bash
qwen --system-file QWEN.md "Read AI_WORKFLOW.md and plan [feature]"
```

---

## What AI does automatically

The AI will:
1. Read `AI_WORKFLOW.md` to understand format and workflow
2. Create tasks in `kanban.md` with strict format
3. Move tasks between columns according to progress
4. Check off subtasks as they are completed
5. Document complete result in `**Notes**:`
6. Reference tasks in Git commits
7. Leave completed tasks in "Done" (archiving on request only)

---

## Traceability and transparency

With this system, you have:

- **Complete history**: Every AI action is documented
- **Easy search**: Grep in Markdown files
- **Statistics**: Velocity, time spent, progress
- **Git links**: Commits reference tasks
- **Collaboration**: Entire team sees what AI does
- **Archives**: Nothing is lost, everything is archived

---

## User Commands

```bash
# Planning
"Plan [feature]"
"Create roadmap for 3 months"

# Execution
"Do TASK-XXX"
"Continue TASK-XXX"

# Tracking
"Where are we?"
"Weekly status"

# Modifications
"Break down TASK-XXX"
"Add subtask to TASK-XXX"

# Search
"Search in archives: [keyword]"

# Maintenance
"Archive completed tasks"
```

---

**[Back to README](../README.md)** | **[Installation](./INSTALLATION.md)** | **[Features](./FEATURES.md)**
