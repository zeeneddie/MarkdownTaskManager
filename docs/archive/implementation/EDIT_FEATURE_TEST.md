# Edit Feature Testing Guide

## Wat is Geïmplementeerd

### ✅ Markdown Serializers
- `serializeEpic(epic)` - Epic object → markdown formaat
- `serializeFeature(feature)` - Feature object → markdown
- `serializeStory(story)` - Story object → markdown
- `serializeTask(task)` - Task object → markdown

### ✅ File Save Functions
- `saveEpic(epic)` - Schrijft epic.md naar epics/EPIC-XXX/ folder
- `saveFeature(feature, epicFolder)` - Schrijft feature.md
- `saveStory(story, epicFolder, featureFolder)` - Schrijft story.md
- `saveTask(task, epicFolder, featureFolder, storyFolder)` - Schrijft TASK-XXX.md
- `saveItem(item)` - Generieke save functie die het juiste type detecteert

### ✅ Edit UI
- Edit knop (✏️) toegevoegd aan alle hierarchy cards
- Edit knop stopt propagatie (triggert geen drill-down)
- Hover effect op edit knop

### ✅ Edit Functionality (Basis)
- `editItem(itemType, itemId)` - Vindt item en opent edit modal
- `openEpicEditModal(epic)` - Simpele prompt voor title edit
- `openFeatureEditModal(feature)` - Simpele prompt voor title edit
- `openStoryEditModal(story)` - Simpele prompt voor title edit
- `openTaskEditModal(task)` - Simpele prompt voor title edit

## Test Scenario's

### Test 1: Epic Title Bewerken
1. Open project-manager.html in Chrome
2. Laad example-project folder
3. Zie epic "EPIC-001 | Technical Assessment & Planning"
4. Klik op ✏️ edit knop (NIET op de card zelf)
5. Prompt verschijnt: "Edit Epic Title"
6. Verander title naar "EPIC-001 | Technical Assessment [TEST]"
7. Klik OK
8. **Verwacht**:
   - Console log: "Saving epic EPIC-001..."
   - Console log: "✓ Epic EPIC-001 saved successfully"
   - Notificatie: "Epic updated successfully"
   - Card toont nieuwe title
   - File `example-project/epics/EPIC-001-assessment/epic.md` is bijgewerkt

### Test 2: Feature Title Bewerken
1. Drill down naar EPIC-001
2. Zie feature "FEATURE-001 | Codebase Quality Analysis"
3. Klik op ✏️ edit knop
4. Verander title naar "FEATURE-001 | Code Quality [TEST]"
5. **Verwacht**:
   - Feature title wordt opgeslagen
   - File wordt bijgewerkt

### Test 3: Story Title Bewerken
1. Drill down naar FEATURE-001
2. Zie story "STORY-001 | Analyze code metrics and complexity"
3. Klik op ✏️ edit knop
4. Verander title
5. **Verwacht**: Story wordt opgeslagen

### Test 4: Task Title Bewerken
1. Drill down naar STORY-001
2. Zie tasks (TASK-001, TASK-002)
3. Klik op ✏️ edit knop van TASK-001
4. Verander title
5. **Verwacht**: Task wordt opgeslagen

### Test 5: Verify File Changes
Na elke edit:
```bash
# Check of file daadwerkelijk is gewijzigd
cat example-project/epics/EPIC-001-assessment/epic.md | head -1
# Moet nieuwe title tonen
```

## Bekende Beperkingen (Huidige Versie)

### Wat WERKT:
✅ Edit knop op alle item types
✅ Item vinden in current items array
✅ Title bewerken via prompt
✅ Markdown serialization (volledig formaat)
✅ File schrijven naar correcte locatie
✅ Breadcrumb context voor path navigation
✅ Success/error notificaties
✅ UI refresh na opslaan

### Wat NOG NIET werkt:
❌ **Full edit modal** - Momenteel simpele prompt, geen modal met alle velden
❌ **Status wijzigen** - Kan alleen title, niet status/priority/etc
❌ **Metadata edit** - Dates, owners, assignments, etc.
❌ **Description edit** - Alleen title in huidige versie
❌ **Acceptance criteria** - Kan niet bewerken
❌ **Story points edit** - Kan niet bewerken
❌ **Steps/subtasks** - Kan niet bewerken
❌ **Dependencies** - Kan niet bewerken

## Volgende Stappen

### Prioriteit 1: Full Edit Modal
Vervang prompt() met een volledige modal met alle velden:
- Title
- Status dropdown (PLANNED, IN_PROGRESS, TESTING, COMPLETED)
- Priority dropdown
- Owner/Assigned
- Dates (created, started, target, completed)
- Description textarea
- Story Points / Hours
- Acceptance Criteria lijst
- Dependencies lijst

### Prioriteit 2: Create New Item
- "New Epic" knop bij epics view
- "New Feature" knop bij features view
- "New Story" knop bij stories view
- "New Task" knop bij tasks view
- Auto-generate ID (EPIC-002, FEATURE-002, etc.)
- Auto-create folder structure

### Prioriteit 3: Delete Item
- Delete knop bij edit modal
- Bevestiging dialog
- Verplaats naar archive? Of permanent delete?
- Wat met children?

### Prioriteit 4: Auto-Aggregation
- Story Points automatisch optellen van children naar parent
- Progress percentage auto-berekenen
- Status auto-update (bijv. epic wordt COMPLETED als alle features COMPLETED zijn)

## Technische Details

### Serializer Voorbeeld
```javascript
serializeEpic({
  id: 'EPIC-001',
  title: 'Technical Assessment',
  status: 'in-progress',
  priority: '🔴 CRITICAL',
  owner: '@eddie',
  spTotal: 34,
  spCompleted: 13,
  progress: 38,
  description: 'Initial assessment...',
  // ...
})
```

Produceert:
```markdown
# EPIC-001 | Technical Assessment

**Parent**: `../../project.md`
**Type**: Epic
**Priority**: 🔴 CRITICAL
**Status**: IN_PROGRESS
**Owner**: @eddie
...
```

### Save Functie Flow
```
editItem('epic', 'EPIC-001')
  → openEpicEditModal(epic)
  → prompt gebruiker
  → epic.title = newTitle
  → saveItem(epic)
  → saveEpic(epic)
  → serializeEpic(epic)
  → File System Access API write
  → Success notificatie
  → renderHierarchy()
```

## Console Output Voorbeeld

Bij successful edit:
```
Edit epic: EPIC-001
Item to edit: {id: 'EPIC-001', title: '...', ...}
Saving epic EPIC-001...
✓ Epic EPIC-001 saved successfully
```

Bij error:
```
Edit epic: EPIC-001
Item to edit: {id: 'EPIC-001', ...}
Saving epic EPIC-001...
Error saving epic: NotAllowedError: User denied permission
```

## Tips voor Testen

1. **Open Chrome DevTools** (F12) om console logs te zien
2. **Test met kopie van example-project** - origineel bewaren als backup
3. **Verify file changes** - Check of markdown bestanden daadwerkelijk veranderen
4. **Test breadcrumb context** - Save functions gebruiken breadcrumbs voor path
5. **Test error handling** - Wat gebeurt er bij permission denied?

