# Test Instructies voor Project Manager

## Vereisten
- Google Chrome (86+), Microsoft Edge (86+), of Opera (72+)
- De `example-project/` folder in deze directory

## Test Stappen

### 1. Open de Applicatie
1. Open `project-manager.html` in Chrome
2. Klik op "Commencer" (Start) knop
3. Selecteer de `example-project/` folder

### 2. Test Epic View (Root Level)
**Verwacht:**
- Je ziet 1 epic: "EPIC-001 | Technical Assessment & Planning"
- De epic toont:
  - Priority: 🔴 CRITICAL
  - Status kolom: IN_PROGRESS
  - Progress bar: 13/34 SP (38%)
  - Target datum: 2025-11-30

**Actie:**
- Klik op de epic card om door te drillen naar features

### 3. Test Feature View
**Verwacht:**
- Breadcrumbs tonen: "🏠 Project › EPIC-001 | Technical Assessment & Planning"
- Je ziet 1 feature: "FEATURE-001 | Codebase Quality Analysis"
- De feature toont:
  - Priority: 🟠 HIGH
  - Status: IN_PROGRESS
  - Progress: 5/13 SP (38%)

**Acties:**
- Test breadcrumb: Klik op "🏠 Project" - je gaat terug naar epics
- Drill-down opnieuw naar EPIC-001
- Klik op FEATURE-001 om door te drillen naar stories

### 4. Test Story View
**Verwacht:**
- Breadcrumbs: "🏠 Project › EPIC-001 › FEATURE-001"
- Je ziet 1 story: "STORY-001 | Analyze code metrics and complexity"
- Story toont:
  - Priority: 🟠 HIGH
  - Status: IN_PROGRESS
  - Story Points: 5 SP
  - Sprint: Sprint 1

**Acties:**
- Test breadcrumb navigatie (klik op verschillende levels)
- Drill-down naar STORY-001 om tasks te zien

### 5. Test Task View
**Verwacht:**
- Breadcrumbs: "🏠 Project › EPIC-001 › FEATURE-001 › STORY-001"
- Je ziet 2 tasks:
  - TASK-001: "Setup code analysis tools" (COMPLETED, 4h)
  - TASK-002: "Run full codebase metrics scan" (IN_PROGRESS, 2h)

**Acties:**
- Probeer op een task te klikken
  - **Verwacht**: Niets gebeurt (of console log: "Tasks have no children")
  - **Reden**: Tasks zijn het laagste niveau, geen children
- Test breadcrumb navigatie terug naar elk niveau

### 6. Test Console Output
Open Chrome DevTools (F12) en check console voor:
- `=== Loading Multi-File Project ===`
- `✓ project.md loaded`
- `✓ Config parsed`
- `Loaded X epics/features/stories/tasks`
- Geen JavaScript errors

## Bekende Beperkingen (Huidige Versie)

### Wat WERKT:
✅ Multi-file folder structure lezen
✅ Drill-down navigatie (Epic → Feature → Story → Task)
✅ Breadcrumb navigatie terug naar hogere levels
✅ Status kolommen (PLANNED, IN_PROGRESS, TESTING, COMPLETED)
✅ Progress bars met Story Point tracking
✅ Metadata weergave (priority, owner, dates, etc.)

### Wat NOG NIET werkt:
❌ Items aanmaken/bewerken/verwijderen (read-only)
❌ Auto-aggregatie van Story Points (handmatig bijgewerkt in files)
❌ Task detail modal bij klikken op task
❌ Filters (category, user, tag, priority)
❌ Zoeken
❌ Archiveren
❌ Dependencies visualisatie
❌ Nederlandse vertalingen (nog Frans)

## Volgende Stappen

1. **File Writers implementeren** - Items kunnen opslaan/bewerken
2. **Auto-aggregatie** - Story Points automatisch optellen van children naar parents
3. **Task detail modal** - Volledige task details tonen bij klikken
4. **Nederlandse vertalingen** - Frans vervangen door Nederlands
5. **Filters en zoeken** - Filteren op verschillende criteria

## Bug Fixes in Deze Versie

### Fix 1: Task Drill-Down Prevention
**Probleem**: Klikken op task probeerde door te drill-down maar tasks hebben geen children
**Oplossing**: Check toegevoegd in `drillDown()` om tasks te stoppen

### Fix 2: Navigate Up Items Reload
**Probleem**: Bij navigeren via breadcrumbs werden items niet herladen
**Oplossing**: `navigateUpTo()` gemaakt async en reload logica toegevoegd

## Testresultaten Notities

_(Gebruik dit gedeelte om je bevindingen te noteren)_

- [ ] Epic view werkt correct
- [ ] Feature view werkt correct
- [ ] Story view werkt correct
- [ ] Task view werkt correct
- [ ] Breadcrumb navigatie werkt in alle richtingen
- [ ] Console toont geen errors
- [ ] Performance is acceptabel voor grote projecten

**Opmerkingen:**

