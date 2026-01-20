# MarQed AI Agent Platform

A multi-stack AI agent platform for automated software development, legacy modernization, code analysis, and project management.

## Features

- **11 AI Agents** - Specialized agents for architecture, quality, testing, documentation, and more
- **Confucius Orchestrator (Fase 23.5)** - Central agent orchestration with PIV loop and quality gates
- **Context Engineering (Fase 23)** - Reference-on-demand system with 60-80% token reduction
- **CWE Security Scanner (Fase 31)** - Multi-scanner suite (OpenGrep, Bandit, Trivy, Custom ASP) with SARIF output
- **Legacy Quickscan (Fase 24-A1)** - 15-minute automated assessment with Go/No-Go recommendation
- **Stage Council Review (Fase 23.6)** - Multi-model LLM reviews at each development stage
- **15+ Workflows** - Green Paper, Brown Paper, migrations, features, bugs, maintenance, stability analysis
- **120+ API Route Files** - Comprehensive REST API with 800+ endpoints (including v2 API + Confucius)
- **40 Dashboards** - Quality, sprints, evolution, estimation, stability, and more
- **290+ Services** - Business logic and analysis engines
- **7 LLM Providers** - Ollama, Groq, Gemini, OpenAI, Anthropic, Qwen, Moonshot
- **5 Extraction Tiers** - Free to Premium with increasing accuracy
- **Stability Analysis** - ASP resource leak detection with 8 categories
- **Legacy Modernization** - 75 gap analysis items across 6 phases (Week 157-244)
- **v2 API (Fase 21.5)** - Decoupled Migration/Quality endpoints with AnalysisContract
- **FP Methodology (Fase 22)** - IFPUG/NESMA compliant Function Point estimation
- **71 Database Migrations** - Comprehensive data model for all features
- **97.8% Test Pass Rate** - 2,700+ tests with comprehensive coverage

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

## Service Management

Use the unified service manager script for development:

```bash
# Start all services
./scripts/marqed-services.sh start

# Stop all services
./scripts/marqed-services.sh stop

# Check status
./scripts/marqed-services.sh status

# Tail all logs
./scripts/marqed-services.sh logs
```

### Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| ChromaDB | 8001 | Vector database (Docker: 8000→8001) |
| Backend API | 8003 | FastAPI REST API |
| Portal | 8004 | MarQed Portal (Next.js) |
| Agents | 8005 | TypeScript agent executor |
| Redis | 6379 | Celery task broker |
| PostgreSQL | 5432 | Main database |
| Ollama | 11434 | Local LLM inference |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MARQED AI PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                  CONFUCIUS ORCHESTRATOR                      │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────────────────┐ │
│  │ Extensions  │ │ Quality    │ │ Workflow Orchestrators  │ │
│  │ (11 Agents) │ │ Gates+PIV  │ │ (4 Types + SSE Stream)  │ │
│  └─────────────┘ └────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  AGENTS: Felix Quinn Betty Eliza Diana Marcus Tessa Miguel  │
│          Peter Paul Vicky                                    │
├─────────────────────────────────────────────────────────────┤
│  WORKFLOWS: GREEN_PAPER | BROWN_PAPER | MIGRATION | QUALITY │
│             STABILITY | ESTIMATION | FEATURE | QUICKSCAN    │
├─────────────────────────────────────────────────────────────┤
│  SECURITY: CWE Scanner | OpenGrep | Bandit | Trivy | ASP    │
├─────────────────────────────────────────────────────────────┤
│  ANALYSIS: Resource Leaks | Security | Performance | Code   │
├─────────────────────────────────────────────────────────────┤
│  STACK: FastAPI + PostgreSQL + ChromaDB + Ollama            │
└─────────────────────────────────────────────────────────────┘
```

### Domain Separation (v2 Architecture)

```
              +-------------------------+
              |  Shared Infrastructure  |
              |  (Stability, Metrics)   |
              +-----------+-------------+
                          |
    +---------------------+---------------------+
    |                     |                     |
    v                     v                     v
+--------+          +----------+          +---------+
| BROWN  |          | MIGRATION|          | QUALITY |
| PAPER  |          | (Exec)   |          | (Valid) |
+--------+          +----------+          +---------+
    |                     |                     |
    +----------+----------+----------+----------+
               |                     |
               v                     v
    +-------------------------------------+
    |       ANALYSIS CONTRACT             |
    | { analysis_id, domains, modules,    |
    |   stability, epics, business_rules }|
    +-------------------------------------+
```

**Key Principle:** Brown Paper and Migration are 100% separated, connected only via the AnalysisContract interface.

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
| [Current Phase](docs/roadmap/phases-current.md) | Week 157 progress |
| [Planned Phases](docs/roadmap/phases-planned.md) | Fase 24-30 roadmap |
| [CWE Security Scanner](docs/roadmap/phases/fase-31-cwe-security-scanners.md) | Multi-scanner security suite (Fase 31 COMPLETE) |
| [Legacy Quickscan](docs/roadmap/phases-current.md#week-157-legacy-quickscan-a1-fase-24-a1--complete) | 15-min Go/No-Go assessment (Fase 24-A1 COMPLETE) |
| [Confucius Orchestrator](docs/architecture/confucius-orchestrator-integration-plan.md) | Central agent orchestration (Fase 23.5 COMPLETE) |
| [GAP Analysis](docs/roadmap/gap-analysis-complete-roadmap.md) | 75-item legacy modernization roadmap |
| [Workflow Separation](docs/architecture/workflow-separation-plan.md) | Brown Paper/Migration/Quality separation (COMPLETE) |
| [FP Methodology](docs/roadmap/phases/fase-22-fp-methodology.md) | IFPUG/NESMA Function Point methodology (COMPLETE) |

## Project Structure

```
MarkdownTaskManager/
├── backend/               # FastAPI application
│   ├── app/              # Application code
│   │   ├── api/          # API routes (113 files, 700+ endpoints)
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic (278 services)
│   ├── tests/            # Test suite (2,557+ tests)
│   └── alembic/          # Database migrations (69)
├── frontend/             # HTML dashboards (40)
├── scripts/              # Utility scripts
│   └── cicd/             # CI/CD pipeline
├── .project/             # Project documentation
└── docs/                 # Additional docs
```

## Development Guidelines

### Requirements Governance (Internal Developers)

Before adding any new requirement or feature to the MarQed.ai platform, follow this process:

```
┌─────────────────────────────────────────────────────────────────┐
│                 NEW REQUIREMENT GOVERNANCE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. EXISTENCE CHECK                                              │
│     └── Does this requirement already exist (fully/partially)?   │
│         ├── Search existing Fases in ROADMAP.md                  │
│         ├── Check gap-analysis-complete-roadmap.md               │
│         └── Review related services in backend/app/services/     │
│                                                                  │
│  2. DECISION TREE                                                │
│     ├── EXISTS FULLY    → Use existing, do not duplicate         │
│     ├── EXISTS PARTIAL  → Extend existing requirement            │
│     └── DOES NOT EXIST  → Proceed to alignment check             │
│                                                                  │
│  3. ALIGNMENT CHECK                                              │
│     └── Does the new requirement align with existing ones?       │
│         ├── Check for conflicts with current architecture        │
│         ├── Verify consistency with existing Fases               │
│         └── Ensure no duplicate functionality under new name     │
│                                                                  │
│  4. DOCUMENT & IMPLEMENT                                         │
│     └── Only after checks pass:                                  │
│         ├── Add to ROADMAP.md with proper Fase number            │
│         ├── Create detailed spec in docs/roadmap/phases/         │
│         └── Reference existing components where applicable       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle:** Build upon what exists. Every new requirement should leverage existing capabilities rather than reinventing them.

| Check | Where to Look |
|-------|---------------|
| Existing Fases | [ROADMAP.md](ROADMAP.md) |
| Gap Analysis Items | [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md) |
| Services | `backend/app/services/` (290+ services) |
| API Endpoints | `backend/app/api/` (800+ endpoints) |
| Database Models | `backend/app/models/` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `make test`
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with FastAPI, PostgreSQL, ChromaDB, and Ollama.
