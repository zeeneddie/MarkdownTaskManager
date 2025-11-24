# Quick Start: Bestaand Project Inchecken & Onderhoudsanalyse

Korte stappen om een bestaand hiërarchisch project (project.md + epics/features/stories/tasks) via de backend te laten analyseren voor maintenance/quality.

## Benodigd
- Docker en docker-compose
- Deze repo gecloned
- Projectmap in hiërarchische structuur (geen kanban.md nodig)

## Stappen
1) **Stack opstarten**
   ```bash
   cd backend
   cp .env.example .env   # pas DATABASE_URL/SECRET_KEY indien nodig
   docker-compose up -d --build
   ```
   Health check: `curl http://localhost:8000/api/health` (docs: `/api/docs`).

2) **Project klaarzetten**
   - Optie A (automatisch, via backend): gebruik de Project API (`POST /api/projects/define`). Dit triggert de `PROJECT_DEFINITION` workflow en maakt de map + `project.md`, `README.md`, `architecture/ARCHITECTURE.md`, `docs/PROJECT_PLAN.md`, `epics/` (met epics) en subdirs (`sprints`, `docs`, `architecture`) aan. Folderpad default `backend/projects/<slug>` tenzij je `folder_path` meegeeft.
   - Optie B (handmatig): maak een nieuwe map en voeg een minimale `project.md` toe met basisfrontmatter. Voorbeeld:
     ```markdown
     # Project: My Project

     **Status**: ACTIVE
     **Start Date**: 2025-11-23
     **Target Date**: 2026-01-15
     **Owner**: @user

     ## Configuration
     **Columns**: 📋 PLANNED | 🚀 IN PROGRESS | 🧪 TESTING | ✅ COMPLETED
     **Priorities**: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW
     **Types**: 📱 FUNCTIONAL, 🔧 TECHNICAL, 🔒 COMPLIANCE, 📊 REPORTING, 🏗️ INFRASTRUCTURE
     **Users**: @user (Name)

     ## Description
     Korte beschrijving...
     ```
   - Maak daarna subfolders `epics/`, en onder epics de hiërarchie `features/`, `stories/`, `tasks/` zoals in `FOLDER_STRUCTURE.md`. Je kunt starten met één lege epic-folder met een `epic.md` (frontmatter met id/titel/status enz.).
   - Als er al een projectmap bestaat: zorg dat het deze hiërarchie volgt (project.md, epics/, features/, stories/, tasks/).
   - Geen kanban.md/archive.md vereist.

3) **Project registreren/syncen**
   - Gebruik de Project API om het project aan te maken en de structuur te synchroniseren (epics/features/stories/tasks) zodat DB en files aligned zijn.
   - Controleer met `GET /api/epics`, `GET /api/features`, etc.

4) **Analyse/maintenance runnen**
   - Start een workflow (bijv. MAINTENANCE of QUALITY_AUDIT) met beschrijving en pad naar je project.
   - Laat de agents de standaard gates draaien (audit → plan → execute → test → document).

5) **Resultaten bekijken**
   - Lees quality/tech-debt/validation outputs en aanbevelingen.
   - Her-run met aangepaste scope of peer-assist indien nodig.

6) **Aanpassingen uitvoeren**
   - Implementeer aanbevolen fixes, draai tests/validation lokaal of via workflow.

7) **Afronden**
   - Commit je wijzigingen (optioneel branch/tag voor deze onderhoudsrun).
   - Houd DB/chroma-containers aan als je doorwerkt; anders `docker-compose down` (met `-v` als je volumes wilt opruimen).

## Notities
- Enkel hiërarchische modus wordt ondersteund; kanban.md/archive.md zijn niet meer nodig.
- UI: gebruik `project-manager.html` of een eigen client die de API aanspreekt voor CRUD en inspectie.
