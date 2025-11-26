# Multi-Stack AI Agent Platform

> **[Version francaise](./readmeFR.md)** | **[Agentic Task Management System](./HERSTART_PROJECT.md)**

**AI-powered multi-stack platform for intelligent task management**

A complete task management system that transforms your Markdown files into an interactive Kanban board, without database or server. Perfect for developers, distributed teams and integration with AI assistants.

> **Week 53 Status (Nov 2025):**
> - Hub Portal live met 12 dashboards
> - 151+ API endpoints operationeel
> - 10 Core AI agents + LLM Council (6 models)
> - Continuous Evolution System complete (A/B Testing, Gradual Rollout, Trend Analysis)
> - Week 54-58: Multi-Stack Platform (multi-project, observability, meta-prompting)
> - Zie `PROJECT_STATUS_SUMMARY.md` voor actuele status

![Application Overview](docs/images/app-overview.jpg)

---

## Project Status: Week 53 COMPLETE

> **Fase 5: Continuous Evolution** COMPLETE
> - **3-Layer Agent Architecture** planned for Week 54-58
> - Hub Portal + 12 dashboards operationeel
> - 151+ API endpoints, 42+ database tables (PostgreSQL via Docker)
> - 10 Core AI agents + LLM Council (6 local Ollama models)
> - A/B Testing Framework + Gradual Rollout + Trend Analysis
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
| **[ARCHITECTURE](./ARCHITECTURE.md)** | Technical overview + links to detail docs |
| **[ROADMAP](./ROADMAP.md)** | 40-week planning |
| **[AGENTS](./AGENTS.md)** | 3-Layer agent architecture reference |

### Architecture Detail Documents

| Document | Description |
|----------|-------------|
| **[Self-Evolution](./docs/architecture/self-evolution.md)** | Self-questioning, navigating, attributing |
| **[A/B Testing](./docs/architecture/ab-testing.md)** | Statistical experimentation framework |
| **[Continuous Evolution](./docs/architecture/continuous-evolution.md)** | Gradual rollout, trend analysis |
| **[LLM Council](./docs/architecture/llm-council.md)** | 6-model consensus decision making |
| **[Multi-Stack Platform](./docs/architecture/multi-stack-platform.md)** | Week 54-58 platform vision |

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

### 3-Layer Agent Architecture (Week 54+)
- **Layer 1: Core Agents** - 10 cross-stack agents (Felix, Quinn, Betty, etc.)
- **Layer 2: Stack Templates** - Per-project agents (Python, JavaScript, Go, Rust)
- **Layer 3: Platform Agents** - ObservabilityEngineer, PromptEngineer, IncidentResponder

### Current Features
- **FastAPI Backend** - 151+ API endpoints, 42+ tables
- **10 Core AI Agents** - Multi-LLM routing (Ollama local + Claude CLI)
- **LLM Council** - 6-model consensus decision making
- **12 Dashboards** - Hub Portal, Agent, Quality Gates, Evolution, etc.
- **Continuous Evolution** - A/B Testing, Gradual Rollout (5%→25%→50%→100%), Trend Analysis
- **Quality Gates** - 28 checks, 8 categories, pre-commit automation
- **ML Training Pipeline** - Effort prediction with experience learning

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

## First Test: Brown Paper Session for Klaverjas

**Doel:** Test de agent-gedreven Brown Paper workflow met het klaverjas-competitie project.

### Prerequisites
1. Backend draait op http://localhost:8000
2. Ollama draait met modellen: `ollama list` (qwen2.5-coder:7b, deepseek-r1, etc.)
3. Project "klaverjas-competitie" bestaat (project_id=1)

### Test Commands

```bash
# 1. Start Green Paper sessie voor project 1
curl -X POST http://localhost:8000/api/week10/sessions \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1}'

# Response: session_id + 6 vragen

# 2. Beantwoord vraag 1 (What problem does this project solve?)
curl -X POST http://localhost:8000/api/week10/sessions/{session_id}/answers \
  -H "Content-Type: application/json" \
  -d '{
    "question_number": 1,
    "answer": "Klaverjas is een Nederlandse kaartspelcompetitie. Dit systeem beheert teams, avonden, scores en standen. Huidige situatie: handmatige Excel sheets, foutgevoelig, geen real-time standen."
  }'

# 3. Beantwoord overige vragen (2-6) met context van CLAUDE.md

# 4. Genereer Constitution (Peter agent)
curl -X POST http://localhost:8000/api/week10/sessions/{session_id}/constitution \
  -H "Content-Type: application/json" \
  -d '{"options": {}}'

# 5. Genereer Specification (Felix agent)
curl -X POST http://localhost:8000/api/week10/constitutions/{constitution_id}/specification \
  -H "Content-Type: application/json" \
  -d '{"options": {}}'

# 6. Genereer Epics (Felix agent)
curl -X POST http://localhost:8000/api/week11/specifications/{specification_id}/epics \
  -H "Content-Type: application/json" \
  -d '{"options": {}}'
```

### Expected Output
- 6 antwoorden → Constitution (project visie)
- Constitution → Specification (HLD)
- Specification → 4-7 Epics met story points
- Eliza agent schat effort per epic

### Validatie
```bash
# Check gegenereerde epics
curl http://localhost:8000/api/project/epics?project_name=klaverjas-competitie

# Vergelijk met handmatig gemaakte epics in:
# Projecten/klaverjas-competitie/EPIC-00*/epic.md
```

### Troubleshooting
- **"Foreign key violation"**: `ALTER TABLE green_paper_sessions DROP CONSTRAINT green_paper_sessions_project_id_fkey;`
- **"Column not found"**: `ALTER TABLE green_paper_sessions ADD COLUMN generation_metadata JSONB;`
- **Ollama timeout**: Check `ollama list` en `ollama serve`

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
