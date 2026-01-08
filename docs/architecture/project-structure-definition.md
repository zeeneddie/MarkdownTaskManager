# Project Structure Definition

**Version:** 1.0.0
**Created:** 2026-01-05
**Status:** APPROVED - Ready for Implementation
**Week:** 145 | Fase 28

---

## Executive Summary

Dit document definieert de professionele directory structuur voor het MarQed AI Agent Platform. De reorganisatie heeft als doel:

1. **Clean root** - Alleen README.md als documentatie
2. **Logische scheiding** - src/backend, src/frontend, tests, config, scripts
3. **Service-based tests** - Niet meer per roadmap week
4. **Robuuste CI/CD** - Snelle en frequente deployments
5. **AI-friendly** - Snelle session bootstrap via .project/QUICKSTART.md

---

## 1. Root Directory (Minimaal)

```
MarkdownTaskManager/
├── README.md                 # ENIGE documentatie in root
├── LICENSE                   # MPL-2.0
├── Makefile                  # Unified commands
├── VERSION                   # Semantic version (e.g., 1.0.0)
├── .gitignore
├── .editorconfig
├── pyproject.toml            # Python project config
└── package.json              # Node.js (minimal)
```

**Regel**: Geen andere .md files in root. Alle documentatie naar `.project/` of `docs/`.

---

## 2. `.project/` - Project Management Hub

Hidden folder voor alle project management documenten. Entry point voor AI assistants.

```
.project/
├── QUICKSTART.md             # Session bootstrap (max 2KB) - LEES EERST
├── STATUS.md                 # Huidige sprint status (max 5KB)
├── ROADMAP.md                # 45-week planning
├── ARCHITECTURE.md           # System architecture
├── AGENTS.md                 # 11 agents reference
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
│
├── ai-configs/               # AI assistant configurations
│   ├── CLAUDE.md
│   ├── CHATGPT.md
│   ├── COPILOT.md
│   ├── QWEN.md
│   └── OPENAI_CLI.md
│
├── kanban/                   # Task management
│   ├── kanban.md             # Active tasks
│   └── archive.md            # Archived tasks
│
└── templates/                # Project templates
    ├── epic-template.md
    ├── story-template.md
    └── sprint-template.md
```

### Session Bootstrap Flow

```
AI Session Start
    │
    ▼
.project/QUICKSTART.md (2KB, 5 sec)
    │ - Project summary
    │ - Directory structure
    │ - Current week focus
    │ - Key commands
    │
    ▼ (if needed)
.project/STATUS.md (5KB, 10 sec)
    │ - Current sprint items
    │ - Blockers
    │ - Recent changes
    │
    ▼ (domain-specific work)
.project/AGENTS.md | ARCHITECTURE.md | etc.

TOTAL BOOTSTRAP: <30 seconds (vs 2-3 minutes huidig)
```

---

## 3. `src/` - Source Code

Alle broncode onder één parent directory.

```
src/
├── backend/                  # Python FastAPI application
│   ├── app/
│   │   ├── api/              # API routes (700+ endpoints)
│   │   │   ├── agents/
│   │   │   ├── analysis/
│   │   │   ├── estimation/
│   │   │   ├── extraction/
│   │   │   ├── migration/
│   │   │   ├── portal/
│   │   │   ├── quality/
│   │   │   ├── sprints/
│   │   │   ├── workflows/
│   │   │   └── __init__.py
│   │   │
│   │   ├── services/         # Business logic (171 services)
│   │   │   ├── agents/
│   │   │   ├── analysis/
│   │   │   ├── estimation/
│   │   │   ├── extraction/
│   │   │   ├── llm/
│   │   │   ├── migration/
│   │   │   ├── observability/
│   │   │   ├── portal/
│   │   │   ├── quality/
│   │   │   └── workflows/
│   │   │
│   │   ├── models/           # SQLAlchemy models (64 files)
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── crud/             # CRUD operations
│   │   ├── providers/        # LLM providers (7)
│   │   ├── core/             # Core framework
│   │   ├── utils/            # Utilities
│   │   └── main.py           # FastAPI entry point
│   │
│   ├── migrations/           # Alembic migrations (68 files)
│   │   └── versions/
│   │
│   └── ml_models/            # Trained ML models
│       ├── fp_effort_*/
│       └── sp_effort_*/
│
├── frontend/                 # Web UI
│   ├── dashboards/           # Dashboard HTML files (40+)
│   │   ├── agent-dashboard.html
│   │   ├── kanban-dashboard.html
│   │   ├── quality-dashboard.html
│   │   └── ...
│   │
│   ├── assets/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── index.html            # Hub Portal entry
│
└── agents/                   # TypeScript agent implementations (optional)
    ├── commands/
    ├── workflows/
    ├── types/
    ├── package.json
    └── tsconfig.json
```

---

## 4. `tests/` - Test Suite (Service-Based)

Tests georganiseerd per service domein, **NIET** per roadmap week.

```
tests/
├── conftest.py               # Pytest configuration
├── pytest.ini                # Pytest settings
│
├── unit/                     # Unit tests per service
│   ├── agents/
│   │   ├── test_agent_service.py
│   │   ├── test_agent_evolution_service.py
│   │   ├── test_felix_integration.py
│   │   └── test_self_navigating.py
│   │
│   ├── analysis/
│   │   ├── test_code_analysis_aggregator.py
│   │   ├── test_dependency_graph_service.py
│   │   ├── test_layered_analysis_service.py
│   │   └── test_trend_analysis_service.py
│   │
│   ├── estimation/
│   │   ├── test_function_points.py
│   │   ├── test_story_points.py
│   │   └── test_estimation_history_service.py
│   │
│   ├── extraction/
│   │   ├── test_deep_extraction_service.py
│   │   ├── test_hierarchical_extraction.py
│   │   ├── test_brown_paper_service.py
│   │   └── test_brown_paper_enhanced.py
│   │
│   ├── llm/
│   │   ├── test_llm_council_service.py
│   │   ├── test_ollama_provider.py
│   │   ├── test_anthropic_provider.py
│   │   └── test_provider_registry.py
│   │
│   ├── migration/
│   │   ├── test_migration_analyzer_service.py
│   │   ├── test_migration_enhanced_service.py
│   │   ├── test_dead_code_detector.py
│   │   └── test_strangler_fig_service.py
│   │
│   ├── models/
│   │   └── test_sqlalchemy_models.py
│   │
│   ├── observability/
│   │   ├── test_cctrace_service.py
│   │   └── test_observability_service.py
│   │
│   ├── portal/
│   │   ├── test_portal_chatbot_service.py
│   │   ├── test_journey_analytics_service.py
│   │   └── test_feature_request_service.py
│   │
│   ├── quality/
│   │   ├── test_quality_gate_service.py
│   │   ├── test_quality_dashboard.py
│   │   ├── test_gradual_rollout_service.py
│   │   └── test_experiment_scheduler.py
│   │
│   ├── schemas/
│   │   └── test_pydantic_schemas.py
│   │
│   ├── sprints/
│   │   ├── test_sprint_service.py
│   │   └── test_sprint_api.py
│   │
│   ├── utils/
│   │   ├── test_guard.py
│   │   └── test_result.py
│   │
│   └── workflows/
│       ├── test_green_paper_workflow.py
│       ├── test_brown_paper_workflow.py
│       ├── test_validation_loop.py
│       └── test_migration_workflow.py
│
├── integration/              # Integration tests
│   ├── api/
│   │   ├── test_health_endpoints.py
│   │   ├── test_sprint_endpoints.py
│   │   └── test_workflow_endpoints.py
│   │
│   ├── database/
│   │   ├── test_migrations.py
│   │   └── test_crud_operations.py
│   │
│   └── providers/
│       ├── test_ollama_integration.py
│       └── test_anthropic_integration.py
│
├── e2e/                      # End-to-end tests
│   ├── workflows/
│   │   ├── test_green_paper_e2e.py
│   │   └── test_brown_paper_e2e.py
│   │
│   └── dashboards/
│       └── test_dashboard_e2e.py
│
└── fixtures/                 # Test data & mocks
    ├── sample_projects/
    │   ├── python_project/
    │   └── dotnet_project/
    │
    ├── mock_responses/
    │   ├── ollama_responses.json
    │   └── anthropic_responses.json
    │
    └── test_data.json
```

### Test Mapping: Week → Service

| Huidige Locatie | Nieuwe Locatie |
|-----------------|----------------|
| `tests/api/week10/` | `tests/unit/workflows/` |
| `tests/api/week11/` | `tests/unit/agents/` |
| `tests/api/week18/` | `tests/unit/quality/` |
| `tests/api/week52/` | `tests/unit/llm/` |
| `tests/services/week10/` | `tests/unit/workflows/` |
| `tests/services/extraction/` | `tests/unit/extraction/` |

---

## 5. `config/` - Configuration

Alle configuratie geconsolideerd.

```
config/
├── docker/
│   ├── docker-compose.yml        # Development
│   ├── docker-compose.prod.yml   # Production
│   ├── Dockerfile
│   └── docker-entrypoint.sh
│
├── environments/
│   ├── .env.example              # Template
│   ├── .env.development
│   ├── .env.staging
│   └── .env.production
│
├── llm/
│   ├── providers.yaml            # Provider registry
│   ├── ollama.yaml
│   ├── anthropic.yaml
│   └── openai.yaml
│
├── agents/
│   ├── felix.yaml
│   ├── quinn.yaml
│   ├── betty.yaml
│   └── ... (11 agents)
│
├── quality/
│   ├── gates.yaml                # Quality gate definitions
│   └── thresholds.yaml
│
├── alembic.ini
└── logging.yaml
```

---

## 6. `scripts/` - Shell Scripts

Alle scripts met duidelijke categorisatie.

```
scripts/
├── start.sh                  # Start all services
├── stop.sh                   # Stop all services
├── status.sh                 # Health check
│
├── dev/                      # Development
│   ├── setup.sh              # Initial setup
│   ├── backend.sh            # Start backend only
│   ├── frontend.sh           # Start frontend dev server
│   ├── db.sh                 # Start databases
│   ├── reset-db.sh           # Reset database
│   ├── seed.sh               # Seed test data
│   └── watch.sh              # File watcher
│
├── test/                     # Testing
│   ├── all.sh                # All tests
│   ├── unit.sh               # Unit tests
│   ├── integration.sh        # Integration tests
│   ├── e2e.sh                # E2E tests
│   ├── coverage.sh           # Coverage report
│   ├── smoke.sh              # Quick smoke test
│   └── parallel.sh           # Parallel execution
│
├── cicd/                     # CI/CD Pipeline
│   ├── _common.sh            # Shared functions
│   │
│   ├── ci/                   # Continuous Integration
│   │   ├── lint.sh           # Linting (ruff, mypy, eslint)
│   │   ├── test.sh           # CI test suite
│   │   ├── security.sh       # Security scan (bandit, safety)
│   │   ├── quality.sh        # Quality gates
│   │   └── validate.sh       # Full CI validation
│   │
│   ├── cd/                   # Continuous Deployment
│   │   ├── build.sh          # Build artifacts
│   │   ├── package.sh        # Package for deploy
│   │   ├── deploy-staging.sh # Deploy to staging
│   │   ├── deploy-prod.sh    # Deploy to production
│   │   ├── rollback.sh       # Rollback
│   │   ├── health-check.sh   # Post-deploy health
│   │   └── notify.sh         # Notifications
│   │
│   ├── docker/               # Docker operations
│   │   ├── build.sh
│   │   ├── push.sh
│   │   ├── compose-up.sh
│   │   └── compose-down.sh
│   │
│   └── release/              # Release management
│       ├── version.sh        # Bump version
│       ├── changelog.sh      # Generate changelog
│       ├── tag.sh            # Git tag
│       └── github-release.sh # GitHub release
│
├── db/                       # Database
│   ├── migrate.sh
│   ├── rollback.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── shell.sh
│
└── utils/                    # Utilities
    ├── clean.sh              # Clean caches
    ├── deps.sh               # Update dependencies
    ├── docs.sh               # Generate docs
    └── env-check.sh          # Validate environment
```

---

## 7. `docs/` - Public Documentation

Openbare documentatie (niet project management).

```
docs/
├── api/                      # API documentation
│   ├── openapi.yaml
│   └── endpoints.md
│
├── architecture/             # Technical architecture
│   ├── overview.md
│   ├── deep-extraction-pipeline.md
│   ├── brown-paper-enhanced.md
│   ├── migration-enhanced.md
│   ├── lrm-platform-integration.md
│   ├── project-structure-definition.md  # THIS FILE
│   └── ...
│
├── guides/                   # User & developer guides
│   ├── installation.md
│   ├── quickstart.md
│   ├── contributing.md
│   └── deployment.md
│
├── roadmap/                  # Roadmap details
│   ├── phases-completed.md
│   ├── phases-current.md
│   └── phases-planned.md
│
└── images/                   # Diagrams & screenshots
    ├── architecture-overview.png
    └── deployment-flow.png
```

---

## 8. `archive/` - Historical Files

Archief voor oude/historische bestanden.

```
archive/
├── docs/
│   ├── week-summaries/       # Week 6-145 summaries
│   │   ├── week-006-009/
│   │   ├── week-010-019/
│   │   └── ...
│   │
│   ├── implementation/       # Historical implementation docs
│   └── planning/             # Old planning docs
│
├── code/
│   ├── agents-typescript-v1/ # Old TS agent code
│   └── deprecated-services/  # Deprecated implementations
│
├── backups/
│   └── pre-rationalisatie-20251116/
│
└── README.md                 # Archive policy & index
```

---

## 9. `.github/` - GitHub Specific

```
.github/
├── workflows/
│   ├── ci.yml                # CI on PR/push
│   ├── cd.yml                # CD on tag
│   └── scheduled.yml         # Scheduled jobs
│
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   └── feature_request.md
│
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS
└── dependabot.yml
```

---

## 10. `.mcp/` - MCP Tool Configurations

```
.mcp/
├── claude/                   # Claude MCP config
├── codex/                    # Codex CLI config
├── serena/                   # Serena MCP config
└── playwright/               # Playwright MCP config
```

---

## 11. Makefile Commands

```makefile
# Development
make start              # Start everything
make stop               # Stop everything
make dev                # Development mode with reload
make setup              # Initial project setup

# Testing
make test               # All tests
make test-unit          # Unit tests only
make test-int           # Integration tests
make coverage           # Coverage report
make smoke              # Quick smoke test

# CI/CD
make lint               # Run linters
make ci                 # Full CI validation
make build              # Build Docker images
make deploy-staging     # Deploy to staging
make deploy-prod        # Deploy to production
make rollback           # Rollback deployment

# Database
make migrate            # Run migrations
make db-reset           # Reset database
make db-backup          # Backup database
make db-shell           # Database CLI

# Utilities
make clean              # Clean caches
make deps               # Update dependencies
make docs               # Generate documentation
```

---

## 12. .gitignore Additions

```gitignore
# Runtime & Cache
__pycache__/
*.py[cod]
.venv/
node_modules/
.mypy_cache/
.pytest_cache/

# Environment & Secrets
.env
.env.*
!config/environments/.env.example
*.pem
secrets/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs & Temporary
*.log
logs/
*.tmp
*.bak

# Database
*.db
chromadb_data/

# ML Models (keep only latest/)
src/backend/ml_models/*/*/
!src/backend/ml_models/*/latest/

# MCP Caches
.mcp/serena/cache/
.mcp/playwright/*.png

# Build artifacts
*.pid
.states/
screenshots/
```

---

## 13. Migration Plan

### Phase 1: Safe Changes (No Breaking)
- [ ] Update `.gitignore`
- [ ] Create `Makefile`
- [ ] Create `scripts/` structure

### Phase 2: Documentation Migration
- [ ] Create `.project/` folder
- [ ] Move MD files from root to `.project/`
- [ ] Create `QUICKSTART.md`
- [ ] Update `README.md` (minimal)

### Phase 3: Archive
- [ ] Create `archive/` structure
- [ ] Move week-specific docs
- [ ] Move deprecated code

### Phase 4: Source Reorganization
- [ ] Create `src/` structure
- [ ] Move backend to `src/backend/`
- [ ] Move frontend to `src/frontend/`
- [ ] Create compatibility symlinks

### Phase 5: Test Reorganization
- [ ] Create new test structure
- [ ] Map week-based tests to service-based
- [ ] Update imports
- [ ] Validate all tests pass

### Phase 6: Config Consolidation
- [ ] Create `config/` structure
- [ ] Move Docker configs
- [ ] Move environment files
- [ ] Update paths in code

### Phase 7: CI/CD Pipeline
- [ ] Create `scripts/cicd/` structure
- [ ] Implement CI scripts
- [ ] Implement CD scripts
- [ ] Update GitHub Actions

### Phase 8: Validation
- [ ] Run full test suite
- [ ] Verify CI pipeline
- [ ] Test deployment flow
- [ ] Update all documentation

---

## 14. Estimated Effort

| Phase | Effort | Risk |
|-------|--------|------|
| Phase 1 | 1 hour | Low |
| Phase 2 | 1 hour | Low |
| Phase 3 | 30 min | Low |
| Phase 4 | 2 hours | Medium |
| Phase 5 | 4 hours | High |
| Phase 6 | 1 hour | Medium |
| Phase 7 | 3 hours | Medium |
| Phase 8 | 2 hours | High |
| **Total** | **~15 hours** | |

---

## 15. Success Criteria

- [ ] Root directory has only 8 files
- [ ] All tests pass (166 files, 2100+ tests)
- [ ] `make start` works
- [ ] `make test` works
- [ ] `make deploy-staging` works
- [ ] AI session bootstrap < 30 seconds
- [ ] CI pipeline completes < 10 minutes
- [ ] Documentation is accurate

---

**Document Owner:** Platform Team
**Review Cycle:** After each major release
**Last Reviewed:** 2026-01-05
