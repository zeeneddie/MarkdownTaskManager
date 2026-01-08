# TC001: Project Intake Flow

**ID**: TC001
**Category**: Onboarding
**Priority**: High
**Status**: ✅ PASSED
**Created**: 2025-11-27
**Last Run**: 2025-11-27

---

## Beschrijving

Test de complete project intake flow: van formulier invullen tot documentatie generatie.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. Project bestaat in `/opt/projecten/hci-crs/src`
3. Geen bestaande registratie voor dit project

## Test Data

| Veld | Waarde |
|------|--------|
| Project Pad | `/opt/projecten/hci-crs/src` |
| Project Naam | `HCI-CRS` |
| Documentatie Pad | (leeg - standaard) |

---

## Test Stappen

### Stap 1: Open Project Intake Pagina

**Actie**: Navigeer naar `http://localhost:8000/project-intake.html`

**Verwacht**:
- Pagina laadt succesvol
- Formulier is zichtbaar met velden:
  - Project Pad (verplicht)
  - Project Naam (verplicht)
  - Documentatie Pad (optioneel)
- "Start Intake" knop is zichtbaar

**Screenshot**: `screenshots/step1_intake_form.png`

### Stap 2: Vul Project Gegevens In

**Actie**:
- Vul Project Pad in: `/opt/projecten/hci-crs/src`
- Vul Project Naam in: `HCI-CRS`
- Laat Documentatie Pad leeg

**Verwacht**:
- Velden accepteren input
- Geen validatie fouten

**Screenshot**: `screenshots/step2_filled_form.png`

### Stap 3: Start Intake

**Actie**: Klik op "Start Intake" knop

**Verwacht**:
- Loading indicator verschijnt
- Formulier wordt verborgen
- Progress tekst toont scan status

**Screenshot**: `screenshots/step3_scanning.png`

### Stap 4: Intake Resultaat

**Actie**: Wacht tot scan compleet is

**Verwacht**:
- "Intake Compleet" header verschijnt
- Statistieken worden getoond:
  - Tech Stacks (verwacht: >0)
  - Components (verwacht: >0)
  - Agents (verwacht: >0)
- Gedetecteerde stacks worden getoond als tags
- Documentatie lijst toont:
  - ✅ README.md
  - ✅ PROJECT_GOAL.md
  - ✅ ARCHITECTURE.md
  - ✅ PROJECT_INTAKE.md

**Screenshot**: `screenshots/step4_result.png`

### Stap 5: Verificatie Documentatie

**Actie**: Controleer of bestanden zijn aangemaakt

**Verwacht**:
- `/opt/projecten/hci-crs/doc/README.md` bestaat
- `/opt/projecten/hci-crs/doc/PROJECT_GOAL.md` bestaat
- `/opt/projecten/hci-crs/doc/ARCHITECTURE.md` bestaat
- `/opt/projecten/hci-crs/doc/PROJECT_INTAKE.md` bestaat

---

## Resultaten

### Run 1 - 2025-11-27 (Initial)

| Stap | Status | Opmerking |
|------|--------|-----------|
| 1 | ✅ Pass | Pagina laadt correct |
| 2 | ✅ Pass | Formulier vooringevuld met HCI-CRS |
| 3 | ✅ Pass | Scan start succesvol |
| 4 | ⚠️ Issue | Stats tonen 0 - API response mist data |
| 5 | ✅ Pass | Documentatie bestond al (handmatig aangemaakt) |

### Run 2 - 2025-11-27 (After Fix)

| Stap | Status | Opmerking |
|------|--------|-----------|
| 1 | ✅ Pass | Pagina laadt correct |
| 2 | ✅ Pass | Formulier vooringevuld met HCI-CRS |
| 3 | ✅ Pass | Scan start succesvol |
| 4 | ✅ Pass | Stats tonen: 3 Tech Stacks, 3 Components, 3 Agents |
| 5 | ✅ Pass | Documentatie correct gegenereerd |

**Gedetecteerde Stacks**: `asp_classic`, `aspnet`, `vbnet`
**Scan Tijd**: 93ms

### Issues Gevonden & Opgelost

1. **ISSUE-001**: ~~Scan API retourneert 0 stacks/components~~ ✅ FIXED
   - **Oorzaak**: Docker container kon `/opt/projecten/` niet benaderen + hardcoded `/app/projects` path
   - **Fix**:
     - `project_registration_service.py` aangepast om `settings.PROJECTS_ROOT` te gebruiken
     - Backend lokaal draaien i.p.v. Docker voor filesystem toegang

---

## Screenshots

| Stap | Bestand |
|------|---------|
| 1 | `screenshots/step1_intake_form.png` |
| 4 | `screenshots/step4_result.png` |
| Final | `screenshots/TC001_intake_success.png` |

---

## Gerelateerde Code

- Frontend: `frontend/project-intake.html`
- API: `backend/app/api/application_registry.py`
- Service: `backend/app/services/application_registry_service.py`
- Templates: `backend/app/services/documentation_templates.py`

---

## Notities

- HCI-CRS is een healthcare EPD systeem met VB.NET, C#, ASP Classic
- Documentatie was handmatig aangemaakt in vorige sessie
- API endpoint werkt maar retourneert geen scan resultaten
