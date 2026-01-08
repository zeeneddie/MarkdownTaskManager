# MarQed AI Agent Platform

A multi-stack AI agent platform for automated software development, legacy modernization, code analysis, and project management.

## Features

- **11 AI Agents** - Specialized agents for architecture, quality, testing, documentation, and more
- **15+ Workflows** - Green Paper, Brown Paper, migrations, features, bugs, maintenance, stability analysis
- **720+ API Endpoints** - Comprehensive REST API for all platform functions
- **35+ Dashboards** - Quality, sprints, evolution, estimation, stability, and more
- **7 LLM Providers** - Ollama, Groq, Gemini, OpenAI, Anthropic, Qwen, Moonshot
- **5 Extraction Tiers** - Free to Premium with increasing accuracy
- **Stability Analysis** - ASP resource leak detection with 8 categories
- **Legacy Modernization** - 75 gap analysis items across 6 phases (Week 151-232)
- **69 Database Migrations** - Comprehensive data model for all features

## Quick Start

```bash
# Clone and setup
git clone https://github.com/zeeneddie/MarkdownTaskManager.git
cd MarkdownTaskManager
make setup

# Start the platform
make start

# Open in browser
open http://localhost:8000
```

## Requirements

- Python 3.12+
- Docker & Docker Compose
- 16GB RAM (development, no GPU required)
- 24GB+ VRAM (production with GPU, optional)

## Commands

| Command | Description |
|---------|-------------|
| `make start` | Start all services |
| `make stop` | Stop all services |
| `make test` | Run all tests |
| `make status` | Check service health |
| `make help` | Show all commands |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MARQED AI PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│  AGENTS: Felix Quinn Betty Eliza Diana Marcus Tessa Miguel  │
│          Peter Paul Vicky                                    │
├─────────────────────────────────────────────────────────────┤
│  WORKFLOWS: GREEN_PAPER | BROWN_PAPER | MIGRATION | FEATURE │
│             STABILITY | QUALITY_GATE | ESTIMATION            │
├─────────────────────────────────────────────────────────────┤
│  ANALYSIS: Resource Leaks | Security | Performance | Code   │
├─────────────────────────────────────────────────────────────┤
│  STACK: FastAPI + PostgreSQL + ChromaDB + Ollama            │
└─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | URL |
|---------|------|-----|
| API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5433 | localhost:5433 |
| ChromaDB | 8001 | http://localhost:8001 |

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](.project/QUICKSTART.md) | Fast bootstrap guide |
| [Architecture](.project/ARCHITECTURE.md) | Technical architecture |
| [Agents](.project/AGENTS.md) | AI agent specifications |
| [Current Phase](docs/roadmap/phases-current.md) | Week 144 progress |
| [Planned Phases](docs/roadmap/phases-planned.md) | Fase 22-29 roadmap |
| [GAP Analysis](docs/roadmap/gap-analysis-complete-roadmap.md) | 75-item legacy modernization roadmap |

## Project Structure

```
MarkdownTaskManager/
├── backend/               # FastAPI application
│   ├── app/              # Application code
│   │   ├── api/          # API routes (700+ endpoints)
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic (170+ services)
│   ├── tests/            # Test suite
│   └── alembic/          # Database migrations
├── frontend/             # HTML dashboards (32)
├── scripts/              # Utility scripts
│   └── cicd/             # CI/CD pipeline
├── .project/             # Project documentation
└── docs/                 # Additional docs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `make test`
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with FastAPI, PostgreSQL, ChromaDB, and Ollama.
