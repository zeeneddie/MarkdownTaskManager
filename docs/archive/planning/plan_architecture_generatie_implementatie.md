# Plan – Architectuur Generatie Implementatie

Doel: Een herhaalbaar proces en tooling om per project automatisch een up-to-date architectuurdocument (`architectuur.md`) te genereren uit de broncode en configuratie, het document lokaal op te slaan én te syncen met de bestaande Chroma/DB-service. Dit betreft applicatie- en software-architectuur (frontend, backend, CI/CD, security), geen infra. Alle secties zijn verplicht.

## Verplichte secties per project
- Context & Domein
- Componenten & Interfaces (incl. externe libs/SDKs)
- Data & Integraties (DB, schema/migrations, externe API’s/brokers/caches, authn/z)
- API-oppervlak (HTTP/WebSocket/CLI; versies; auth)
- Frontend (entrypoints, build/serve, UI-tech, integratiepunten)
- Backend (frameworks, routers/controllers, services, jobs/schedulers)
- CI/CD (pipelines, quality gates, tests/lint/typecheck, artefacten, deploy-stappen)
- Deploy/Runtime (processen/containers, ENV/ports, healthchecks, configbronnen)
- Security (authn/authz, secrets, netwerktoegang, deps, risico’s)
- NFR’s (performance, availability, observability/logging, privacy/offline)
- Risico’s & Unknowns
- Versiebeheer/branching-strategie
- Business Logica/Domein (kernprocessen, domeinmodellen, belangrijkste regels/invarianten)

## Stappenplan (6 fasen)

### 1) Sjabloon & paden vastleggen
- Doel: Eén standaard Markdown-sjabloon en bestandsnaam (`architectuur.md`) per project-root.
- Taken:
  - Definieer de sectievolgorde en standaard kopjes (bovenstaande lijst).
  - Kies opslagpad: `{project_root}/architectuur.md`.
  - Voorzie placeholders voor “unknowns/TODO”.
- Pseudo-implementatie:
  - Bash/Python: schrijf statisch sjabloonbestand naar project-root als het nog niet bestaat.
- DoD:
  - Sjabloonbestand beschikbaar; gedeelde secties aanwezig; bestandsnaam/pad vastgelegd.

### 2) Extractors bouwen (code & config scannen)
- Doel: Automatisch feiten verzamelen uit de codebase.
- Taken (minimaal):
  - Routers/controllers: `rg "^@router" backend/app/api` → lijst endpoints, tags.
  - Services/jobs: scan `backend/app/services`, `scheduler`, cron/startup hooks.
  - Modellen/migrations: lees `models` + `alembic/versions` om DB/tabellen te identificeren.
  - Dependencies: parse `requirements.txt`, `package.json`, detect frameworks (FastAPI, SQLAlchemy, KaibanJS, etc.).
  - Frontend: detecteer entry (bijv. `task-manager.html`), dashboard HTML’s, build/serve scripts.
  - CI/CD: detecteer GitHub Actions/GitLab CI/Makefiles/run-scripts (lint/test/coverage).
  - Deploy/runtime: parse `docker-compose.yml`, `Dockerfile`, entrypoints, ports, volumes, ENV.
  - Security/auth: zoek JWT/OAuth config, auth middleware, secretsgebruik, CORS.
  - Branching: optioneel uit `README`/`CONTRIBUTING`/CI-conventies.
- Pseudo-implementatie:
  - Python scripts die `subprocess` met `rg` aanroepen en resultaten structureren (JSON).
  - Eenvoudige parsers voor YAML (docker-compose), JSON (package.json), ini/toml waar nodig.
  - Geen extra tools tenzij nodig; vraag toestemming voor nieuwe deps.
- DoD:
  - Script(s) leveren gestructureerde output (JSON/dict) met gevonden feiten per domein.

### 3) Synthese: feiten naar Markdown invullen
- Doel: Vul `architectuur.md` met de gevonden feiten + unknowns.
- Taken:
  - Lees sjabloon; vervang placeholders met extractor-output.
  - Markeer ontbrekende info expliciet als TODO/unknown.
  - Voeg tabellen/lijsten voor API’s, componenten, datastores, pipelines, risico’s.
- Pseudo-implementatie:
  - Python: jinja2-achtig templating (zonder externe deps: string `.format` of minimal template) die JSON-output naar Markdown mapt.
  - Schrijf naar `{project_root}/architectuur.md`; behoud handmatige edits door markers of merge-strategie (bijv. secties volledig regenereren, rest behouden).
- DoD:
  - Volledig gevulde Markdown met alle verplichte secties; unknowns expliciet benoemd.

### 4) Opslag & synchronisatie
- Doel: Artefact lokaal én in Chroma/DB beschikbaar maken voor zoekbaarheid.
- Taken:
  - Bewaar `architectuur.md` in de project-root (Git).
  - Roep bestaande sync-service aan om het document + metadata te indexeren (projectnaam, datum, versie).
- Pseudo-implementatie:
  - Bash/Python: POST naar interne sync-service endpoint met payload (path/content/project-id).
  - Fallback: schrijf een JSON manifest voor batch-sync.
- DoD:
  - Bestaat lokaal; bevestigde call naar sync-service (of queued manifest) succesvol.

### 5) Automatische triggers bij work-items
- Doel: Bij elke Epic/Feature/User-Story/Task wijzigingen detecteren en zo nodig hergenereren.
- Taken:
  - Koppel event-hook (bestaand in het systeem) om bij aanpassingen in code/config de extractor + synthese te draaien.
  - Filter op relevante diffs (routers/models/deps/CI/compose) om noise te beperken.
  - Log diffs in Chroma/DB of maak een review-taak als handmatige check gewenst is.
- Pseudo-implementatie:
  - Python hook die bij een event `git diff` op relevante paden doet; bij impact: run extractors + update `architectuur.md` + sync.
  - Optioneel: sla diff-samenvatting op.
- DoD:
  - Trigger draait bij relevante work-item events; impact leidt tot bijgewerkt document + sync/log.

### 6) Review & kwaliteitsborging
- Doel: Zorgen dat het document bruikbaar en consistent blijft.
- Taken:
  - Validatie-run: check dat alle verplichte secties gevuld zijn (of TODO-label).
  - Minimal lint: Markdown link-check op interne referenties, sectie-aanwezigheid.
  - Reviewstap door architect/analist voor acceptatie.
- Pseudo-implementatie:
  - Python check die sectiekoppen valideert en TODO’s telt.
  - Bash: simpele link-checker (optioneel) op relatieve paden.
- DoD:
  - Validatierapport zonder blocking errors; review gebeurd of gepland.

## Randvoorwaarden & keuzes
- Talen/tools: Python + Bash; `rg` voor snelle zoekopdrachten. Extra tools/deps alleen na akkoord.
- Bestandsnaam: altijd `architectuur.md` in project-root.
- Sync-service: aangenomen aanwezig; beschrijf aanroep, geen implementatie nodig.
- Mono/multi-service: per repo één document; verwijzingen naar andere repos/services/libs expliciet in sectie “Componenten & Interfaces” en “Data & Integraties”.
- Geen infra-scope: infra (cloud/K8s) buiten beschouwing, behalve wat nodig is voor deploy/runtime vanuit compose/Dockerfile.

## Definition of Done (voor implementatie van dit plan)
- Sjabloon geleverd en vastgelegd.
- Extractor-script(s) leveren JSON-feiten voor routers/services/models/deps/CI/compose/frontend/security.
- Generator schrijft `architectuur.md` met alle verplichte secties (unknowns toegestaan maar gemarkeerd).
- Sync-call of manifest aangemaakt voor centrale index.
- Event-hook aanwezig die bij work-item impact her-run triggert.
- Validatie/check aanwezig; document door een architect reviewbaar zonder extra vragen.

## Meta-prompting aanpak (gefaseerde LLM-sturing)
- Doel: iteratief prompten zodat elke fase de volgende voedt en aannames worden vermeden.
- Werkwijze per fase:
  - Fase 1 (Context/stack): prompt met alleen kernbestanden (requirements/package.json, docker/compose, CI config) en vraag om stack + belangrijkste paden.
  - Fase 2 (API/routers): voer de door fase 1 gevonden routerbestanden aan en vraag om API-samenvatting (endpoints/tags/auth).
  - Fase 3 (Models/data): voer migrations/models in; vraag om datastores, tabellen, relaties.
  - Fase 4 (Business logica/domein): gebruik services/usecases/domain-bestanden; vraag om kernprocessen, domeinmodellen, belangrijkste regels/invarianten.
  - Fase 4 (Frontend): gebruik front-entry HTML/JS; vraag om build/serve en integratiepunten.
  - Fase 5 (CI/CD): gebruik pipeline configs; vraag om lint/test/type/coverage/deploy.
  - Fase 6 (Security): gebruik auth/config; vraag expliciet om authn/z, secrets, CORS, externe calls.
  - Synthese: combineer outputs in sjabloon; onbekend = TODO/unknown.
- Promptregels:
  - Vraag om alleen feitelijke claims met bron (bestand/pad); bij twijfel: markeer unknown.
  - Beperk input per prompt tot relevante snippets (geen hele repo).
  - Hergebruik eerdere bevindingen expliciet in de volgende prompt (“Given stack X and routers Y, summarize APIs”).
