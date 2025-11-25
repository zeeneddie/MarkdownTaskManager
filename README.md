# Markdown Task Manager

> **[Version francaise](./readmeFR.md)** | **[Agentic Task Management System](./HERSTART_PROJECT.md)**

**Kanban task manager based on local Markdown files**

A complete task management system that transforms your Markdown files into an interactive Kanban board, without database or server. Perfect for developers, distributed teams and integration with AI assistants.

> **Week 50 Status (Nov 2025):**
> - Hub Portal live met 12 dashboards
> - 151 API endpoints operationeel
> - 10 AI agents (100% local via Ollama)
> - Quality Gate Integration & Agent Validation Loop shipped
> - Zie `PROJECT_STATUS_SUMMARY.md` voor actuele status

![Application Overview](docs/images/app-overview.jpg)

---

## Project Status: Week 50 COMPLETE

> **Fase 4: UI + Intelligence** in progress
> - Hub Portal + 12 dashboards operationeel
> - 151 API endpoints, 39 database tables (PostgreSQL via Docker)
> - 10 AI agents, 6 Ollama models (~25GB)
> - Quality Gate Integration & Agent Validation Loop
> - ChromaDB for experience storage
> - [Full roadmap](./ROADMAP.md) | [Architecture](./ARCHITECTURE.md)

---

## Quick Start

```bash
# 1. Download task-manager.html
# 2. Open in Chrome/Edge/Opera
# 3. Select a folder for your tasks
```

**That's all!** The app creates `kanban.md` and `archive.md` automatically.

**Requirements:** Chrome 86+, Edge 86+, or Opera 72+ ([why?](./docs/COMPATIBILITY.md))

---

## What is it?

```
task-manager.html  -->  Browser  -->  Your Markdown files
    (single file)     (Chrome/Edge)    (kanban.md + archive.md)
```

**Key benefits:**
- **Single file** - Easy to copy, share and maintain
- **100% local** - Your data stays on your machine
- **Git compatible** - Versionable, syncable, diffable
- **AI ready** - Works with Claude, ChatGPT, Copilot, Gemini
- **No server** - Works entirely in the browser

> **Agentic Features**: 10 AI agents, 9 work type workflows, quality gates, ML estimation pipeline

---

## Documentation

| Document | Description |
|----------|-------------|
| **[Installation](./docs/INSTALLATION.md)** | Setup options, HTML management, migration guides |
| **[Features](./docs/FEATURES.md)** | All 9 features: Kanban, filters, archives, multi-project |
| **[AI Integration](./docs/AI_INTEGRATION.md)** | Claude, ChatGPT, Copilot, Gemini setup |
| **[Configuration](./docs/CONFIGURATION.md)** | Columns, categories, tags, users customization |
| **[Use Cases](./docs/USE_CASES.md)** | Dev teams, personal use, distributed teams scenarios |
| **[Compatibility](./docs/COMPATIBILITY.md)** | Browser support, performance, security |

### Agentic System Documentation

| Document | Description |
|----------|-------------|
| **[PROJECT_STATUS_SUMMARY](./PROJECT_STATUS_SUMMARY.md)** | Start here - current status |
| **[ARCHITECTURE](./ARCHITECTURE.md)** | Technical deep dive |
| **[ROADMAP](./ROADMAP.md)** | 40-week planning |
| **[AGENTS](./AGENTS.md)** | 10 AI agents reference |

---

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **Interactive Kanban** | Drag & drop, customizable columns |
| **Task Management** | Rich metadata, subtasks, auto-save |
| **Advanced Filters** | Priority, tags, categories, users |
| **Archive System** | History, search, restore |
| **Multi-Project** | 10 recent projects, quick switch |
| **AI Integration** | 7 AI assistants supported |
| **Multi-language** | English + French |
| **Global Search** | Find tasks instantly |
| **Auto-Save** | No save button needed |

[See all features in detail](./docs/FEATURES.md)

---

## Agentic Task Management System

This repository includes an **AI-powered agentic system** with:
- **FastAPI Backend** - 151 API endpoints, 39 tables
- **10 AI Agents** - 100% local (Ollama, 6 models)
- **LLM Council** - Multi-model consensus voor kritieke beslissingen (NEW!)
- **12 Dashboards** - Hub Portal, Agent, Quality Gates Config, Evolution, etc.
- **16 SuperClaude Commands** - Domain expertise
- **Quality Gates** - 42 validation rules + Integration & Validation Loop
- **ML Training Pipeline** - Effort prediction
- **A/B Testing Framework** - Continuous agent evolution

[Read the complete guide](./HERSTART_PROJECT.md)

---

## Database & Infrastructure

**PostgreSQL (Docker)**
- 39 tables for task management, agents, quality gates, A/B testing
- Docker container: `project_manager_db` on port 5433
- Credentials: `user:password` (configurable via `.env`)

**ChromaDB (Docker)**
- Experience storage for agent evolution
- Container: `project_manager_chromadb` on port 8001
- Persistent storage for agent learning

**Quick Start:**
```bash
cd backend
docker-compose up -d db chromadb  # Start databases
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Start API
```

[See full setup guide](./HERSTART_PROJECT.md)

---

## LLM Council: Multi-Model Decision Making

**"Wisdom of crowds" for critical decisions**

Instead of relying on a single AI model, the **LLM Council** consults 5-6 local Ollama models simultaneously for:
- Architecture & design decisions
- Epic/Feature/Story generation validation
- Quality gate override assessments
- Project planning & resource allocation

**3-Stage Process:**
1. **Response** - Query all models in parallel
2. **Peer Review** - Models anonymously evaluate each other's answers
3. **Synthesis** - Chairman model (deepseek-r1) creates final consensus

**Example Use Cases:**
- "Should we use microservices or monolith?" → 6 models debate → Consensus decision
- "Is this quality gate override safe?" → Risk assessment from multiple perspectives
- "Are these user stories complete?" → Multi-model validation

**Benefits:**
- Reduces single-model bias
- Catches blind spots and edge cases
- Provides dissenting opinions for edge cases
- Higher confidence in critical decisions

[Read full integration plan](./docs/roadmap/active/LLM_COUNCIL_INTEGRATION.md)

---

## AI Assistants Integration

Works with all major AI assistants:

| AI | Config File |
|----|-------------|
| Claude | `CLAUDE.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| ChatGPT | `CHATGPT.md` |
| Gemini | `.gemini/instructions.md` |
| OpenAI CLI | `OPENAI_CLI.md` |
| Qwen | `QWEN.md` |
| Windsurf/Codeium | `.windsurf/instructions.md` |

[Complete AI setup guide](./docs/AI_INTEGRATION.md)

---

## File Structure

```
your-project/
├── kanban.md          # Active tasks (required)
├── archive.md         # Archived tasks (required)
├── AI_WORKFLOW.md     # AI guidelines (optional)
└── CLAUDE.md          # AI config (optional)
```

---

## Templates

| Template | Purpose |
|----------|---------|
| [`kanban.md`](./examples/kanban.md) | Base kanban template |
| [`archive.md`](./examples/archive.md) | Archive template |
| [`AI_WORKFLOW.md`](./AI_WORKFLOW.md) | AI workflow guidelines |

---

## Roadmap

### Current: v1.0
- Interactive Kanban, task management, filters, archives, multi-project, AI integration

### Next: v1.1
- Dark mode, keyboard shortcuts, PDF export, visual statistics

### Future: v2.0
- Offline mode, cross-device sync, IDE plugins, REST API

---

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/my-feature`)
3. Modify `task-manager.html`
4. Test in Chrome, Edge, Opera
5. Create a Pull Request

[Contribution guidelines](./docs/INSTALLATION.md#advanced-installation)

---

## License

**Mozilla Public License 2.0 (MPL-2.0)**

See [LICENSE](./LICENSE) file for details.

---

## Support

- **Questions?** Open an issue on GitHub
- **Bugs?** Create an issue with `bug` tag
- **Suggestions?** Create an issue with `enhancement` tag

---

**Created with love for those who value simplicity, data ownership, and transparency.**
