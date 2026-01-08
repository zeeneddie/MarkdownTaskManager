# Architectuur – Markdown Task Manager

## Systeemcontext
- Frontend: single-file UI (`task-manager.html`) + dashboard HTML’s in `frontend/`, statisch bediend door de backend.
- Backend: FastAPI (async), JWT-auth, Postgres, optional ChromaDB voor experience store, scheduler, WebSocket.
- Data-bron: Markdown (`kanban.md`, `archive.md`) blijft leidend; DB biedt snelheid/analytics voor agents.
- AI/Agents: 10 lokale agents (Ollama, 100% lokaal, geen cloud-calls) met workflows (nieuw feature, bug, maintenance, quality, etc.), self-evolution/validation (week 17-26).

## Componenten
- UI: KaibanJS-kanban, filters, autosave; extra dashboards (sprint, agent, quality, estimation, maintenance, wizard).
- API: CRUD op epics/features/stories/tasks/sprints/users; workflows; estimations; scheduler; week10/11 generators; wizard.
- Services: Scheduler service, ML training, estimation calculators, quality gates, task generation (deels uitgeschakeld wegens OpenAPI-issues).
- Storage: Postgres (kernentities), ChromaDB (ervaring/patronen), Markdown files (user-facing bron), embeddings/ML-artifacten.
- Deploy: `docker-compose` (Postgres 15, ChromaDB, API). Frontend gemount in container op `/frontend`.

## Belangrijke paden
- Static/dashboards: `/frontend/*.html` via FastAPI static mount.
- Health: `/api/health`; API docs: `/api/docs`.
- Kern-routers actief: auth, project/epics/features/stories/tasks/sprints, workflows, projects, estimation, estimation_history, wizard, scheduler, week10 green-paper, week11 task generation.
- Voor nu uitgeschakeld (OpenAPI fix nodig): websocket, maintenance, ml_training, evolution, quality_dashboard, self_navigating, attribution, task_generation (week23-24), continuous_learning, rollback.

## Datamodel (beknopt)
- Markdown: kolommen + metadata (prio, tags, assignee, due).
- DB: Item hiërarchie (Epic/Feature/Story/Task), sprint, user, green-paper/spec-kit entities, estimation history, scheduler jobs, experience data (indien ingeschakeld).

## Stromen
- Standalone gebruik: open `task-manager.html` → lees/schrijf `kanban.md`/`archive.md`.
- Met backend: dashboards en API roepen Postgres/Chroma aan; agents/workflows gebruiken DB + experience store; scheduler start onderhoud/quality jobs.
- Embeddings/ML: ChromaDB voor experience store; Torch/transformers voor ML-training (kan zwaar zijn). LLM-inference loopt via Ollama lokaal.

## Beheer & observability
- Alembic migrations in entrypoint; logs via docker-compose; geen full observability stack.
- CORS open (config); JWT-secret vereist.

## Risico’s / aandachtspunten
- OpenAPI breekt als uitgeschakelde routers teruggezet worden zonder schema-fix; vermoedelijk ongedefinieerde dict/Any modellen in die modules.
- Docker-image groot (Torch/transformers); overweeg optional build of aparte ML-service.
- Auto-migraties bij start (entrypoint) zijn dev-vriendelijk maar in prod liever CI/CD-run.
- Auth zonder uitgebreide RBAC/tenancy; security-harde randvoorwaarden nog basic.
