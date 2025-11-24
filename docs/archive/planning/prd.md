# Product Requirements Document – Markdown Task Manager

## Doel & scope
- Maak Markdown-taken bruikbaar als interactieve kanban, 100% lokaal, zonder server of database-setup.  
- Optioneel: FastAPI-backend voor geavanceerde agentische workflows (planning, schatting, quality gates).
- Bewaar bron-van-waarheid in Markdown (`kanban.md`, `archive.md`); alles moet leesbaar blijven in Git.

## Doelgroepen
- Developers/teams die taken in Markdown beheren en Git gebruiken.
- AI-assisted workflows (lokaal via Ollama) voor planning/kwaliteit/schattingen.
- Offline/low-ops gebruik: enkel `task-manager.html` openen moet voldoende zijn.

## Kernproblemen die we oplossen
- Geen vendor lock-in of database nodig voor basis-tasking.
- Eén bestand UI (`task-manager.html`) dat direct op Markdown werkt.
- Agents (10 rollen) voor audits, schattingen, bugfixing en documentatie, allemaal lokaal.

## Functional requirements
- Kanban UI (drag/drop), kolommen, tags, prioriteiten, assignees; autosave naar `kanban.md`.
- Archiveren/herstellen naar `archive.md`.
- Filters/zoekfunctie op tags/prio/status/assignee.
- Multi-project selector (recente projecten).
- AI/agent workflows (backend):
  - Work-type routing (9 workflows).
  - Function/Story point schattingen.
  - Quality gates & scheduler endpoints.
- Dashboards (served door backend): sprint/agent/quality/estimation/maintenance wizard.

## Niet-scope / later
- Sync tussen devices, realtime collaboration buiten WebSocket.
- Public cloud AI modellen.
- Productie-grade authz/tenant-scheiding (nu enkel JWT-authn).

## Data & modellen
- Markdown schema: kolommen (To Do/In Progress/Done), metadata (prio, tags, assignee, due, links).
- DB (backend): hiërarchie Epic→Feature→Story→Task; sprints; users; embeddings/experience store (ChromaDB).

## Integraties
- AI lokalen modellen (Ollama) voor agents.
- ChromaDB voor ervaring/patronen (self-evolution).
- Postgres voor kern-entities en metrics.

## Niet-functioneel
- Privacy/offline: frontend werkt standalone; backend draait met lokale LLMs via Ollama, geen externe API-calls.
- Performance: UI responsief op ~1k tasks; backend async FastAPI, Postgres indexes.
- Deploybaarheid: `docker-compose` met Postgres + ChromaDB + API; single HTML voor frontend.

## Succes-metrics (indicatief)
- Time-to-first-board < 2 min (download/open HTML).
- ≥80% test pass op backend pipelines.
- Eerste OpenAPI-load zonder fouten; dashboards laden zonder 404.

## Openstaande risico’s
- Sommige geavanceerde agent-routes staan uit ivm OpenAPI compatibiliteit; her-inschakelen vereist schema-fix.
- Docker-image zwaar door Torch/transformers; kan resource-hongerig zijn.
- Auth is JWT maar geen uitgebreide RBAC/tenant-scheiding.
