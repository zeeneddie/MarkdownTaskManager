# Plan – Workflow & Agent Improvements (stack-aware)

Doel: Workflows uitbreiden met nieuwe rollen (UX/Frontend/Backend/Integratie), standaard validation gates, security checks, en stack-specifieke varianten. Klaar voor implementatie.

## Scope
- Workflows: NEW_FEATURE, ENHANCEMENT, MIGRATION, QUALITY_AUDIT, BUG, MAINTENANCE (en optioneel TESTING).
- Rollen: UX Designer, Frontend Developer (Blazor/HTML/CSS/JS/TS), Backend Developer (.NET Core/C#, CQRS, SQL Server), Integratie Specialist (contract/integratietests).
- Validation: lint/type/test/coverage + security/dep-check per workflow.
- Stack-specifiek: per project agent-set kiezen op basis van techstack.

## Verbeteringen per workflow (minimaal)
- NEW_FEATURE / ENHANCEMENT:
  - Rollen: +UX, +Frontend, +Backend, +Integratie waar nodig.
  - Gated: lint/type/test/coverage; UI check; contract/integratie bij externe koppelingen; security depscan.
  - Deliverables: ontwerp/UX artefacten, API/contract, tests (unit/UI/contract).
- MIGRATION:
  - Rollen: +Integratie, +Backend; UI indien frontends wijzigen.
  - Gated: lint/type/test/coverage; migratie-checks (schema compat, data scripts); contract/integratie; security depscan.
  - Deliverables: migratieplan, rollbackplan, validatieverslag.
- QUALITY_AUDIT:
  - Rollen: Quinn + (optioneel Integratie voor contracten, Backend voor API review, Frontend voor UI issues).
  - Gated: security (SAST/deps), quality gates, contract sanity.
  - Deliverables: risicorapport + prioriteiten.
- BUG:
  - Rollen: Betty + Tessa + Diana; voeg Backend/Frontend/Integratie toe afhankelijk van de bug surface.
  - Gated: regression test vereist; lint/type (scope) + dep-check waar relevant.
- MAINTENANCE:
  - Rollen: Marcus + Quinn + Tessa + Eliza; voeg Integratie/Backend/Frontend bij refactors van respectievelijk API/UX.
  - Gated: lint/type/test/coverage; security depscan; contract checks bij dependency updates.
- TESTING:
  - Rollen: Tessa + (Quinn audit) + Diana; optioneel Integratie voor contract tests.
  - Gated: test focus; coverage rapportage.

## Validation gates (standaard)
- Lint + Typecheck + Unit tests + (waar zinvol) UI/contract/E2E.
- Security/dep-check (Python: pip-audit/bandit; JS/TS: npm audit; .NET: dotnet list package --vuln).
- Coverage: minimaal drempel per workflow (bv. 70-80% waar passend).
- Optional: contract tests voor externe API’s/clients (voor Integratie Specialist).

## Stack-specifieke varianten (voorbeeld)
- Frontend: Blazor/HTML/CSS/JS/TS; gebruik bijpassende lint/build/test (eslint/prettier/tsc of Blazor toolchain).
- Backend: .NET Core/C#, CQRS (MediatR), EF Core, SQL Server; logging (Serilog/Seq); Swagger/OpenAPI; tests (xUnit/FluentAssertions); FluentValidation; Docker/Compose.
- Git workflow: feature branches, korte-lived branches, PR-review, consistente branch/commit conventies.

## Implementatie-aanpak
1) Document updates:
   - AGENTS.md: nieuwe rollen + stack hints (al aanwezig, uitbreiden met workflow-inzet).
   - AI_WORKFLOW.md (of nieuw hoofdstuk): per workflow rol-toewijzing + gates + stack-notes.
   - planning.md: actiepunt om per project agent-set/stack te kiezen.
   - README.md: verwijzing dat het plan klaarstaat.
2) Configuratie per project:
   - Nieuw configbestand (bijv. `workflow_config.json`) met: techstack, benodigde roles, minimale gates (lint/type/test/security/coverage/contract).
3) Tooling:
   - Scripts/hooks om bij Epic/Feature/User-Story/Task diff-detectie te doen en de juiste gates/rollen te activeren.
   - Security/dep-check commands per stack (dotnet list package --vuln; npm audit; pip-audit/bandit).
4) Review/ops:
   - Architect review van workflow-mapping per project.
   - Log/rapportage van uitgevoerde gates.

## Definition of Ready (voor implementatie)
- Rollen en workflow-uitbreidingen beschreven in AGENTS.md + AI_WORKFLOW.md.
- Config-schema voor project-specifieke agent-set/gates gedefinieerd.
- Documentatie links in README.md/planning.md aanwezig.

## Definition of Done (implementatie)
- Workflow-definities geüpdatet (rollen, gates, stack-notes) en gepubliceerd.
- Per project: config aanwezig met gekozen stack/rollen/gates.
- Hooks/scripts voor gate-executie en security/dep-checks beschikbaar.
- Communicatie in README/planning verwijst naar dit plan en status.***
