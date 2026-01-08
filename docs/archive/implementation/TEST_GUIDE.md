# Test Gids - Sync Engine

## 🧪 Beschikbare Tests

### Test 1: Roundtrip Test (Parse → Generate → Parse)
Verifieert dat alle data behouden blijft door de cyclus.

```bash
python3 backend/app/sync/test_roundtrip.py
```

**Verwacht resultaat:**
```
🎉 ROUNDTRIP TEST PASSED!
✅ SUCCESS: Perfect roundtrip!
```

---

### Test 2: Sync Engine Test (Volledige workflow)
Test de complete sync workflow zonder database.

```bash
python3 backend/app/sync/test_sync_engine.py
```

**Verwacht resultaat:**
```
🎉 SYNC ENGINE TEST COMPLETE!
✅ All sync workflow steps verified
```

---

### Test 3: File Watcher Test (Live monitoring)
Test auto-sync door bestanden aan te passen.

```bash
python3 backend/app/sync/test_watcher_live.py
```

**Wat gebeurt er:**
1. Script start file watcher
2. Open een .md bestand in `Projecten/MarkdownTaskManager/`
3. Maak een wijziging en sla op
4. Zie hoe de sync automatisch wordt getriggerd!

**Stop met:** `Ctrl+C`

---

### Test 4: Handmatige Parser Test
Test of de parser de nieuwe structuur correct leest.

```bash
cd backend/app/sync
python3 -c "
from parser import MultiFileProjectParser
from pathlib import Path

parser = MultiFileProjectParser(Path('/home/eddie/Projects/MarkdownTaskManager'))
project = parser.parse_project()

print(f'Epics: {len(project[\"epics\"])}')
print(f'Features: {len(project[\"features\"])}')
print(f'Stories: {len(project[\"stories\"])}')
print(f'Tasks: {len(project[\"tasks\"])}')

for epic in project['epics']:
    print(f'\\n{epic[\"id\"]}: {epic[\"title\"]}')
"
```

---

### Test 5: Nieuwe Epic Genereren
Test of de generator correct markdown genereert.

```bash
cd backend/app/sync
python3 -c "
from generator import MultiFileProjectGenerator
from pathlib import Path

generator = MultiFileProjectGenerator(Path('/home/eddie/Projects/MarkdownTaskManager'))

test_epic = {
    'id': 'EPIC-TEST',
    'type': 'epic',
    'title': 'Test Epic',
    'status': 'PLANNED',
    'priority': 'LOW',
    'phase': 'INITIATIE',
    'owner': 'tester',
    'sp_total': 0,
    'sp_completed': 0,
    'epic_type': 'FUNCTIONAL',
    'description': 'Dit is een test epic',
    'business_value': 'Test de generator',
    'tags': ['test'],
    'features': []
}

generator.generate_epic(test_epic)
print('✅ Test epic gegenereerd in Projecten/MarkdownTaskManager/EPIC-TEST/')
"
```

**Cleanup:**
```bash
rm -rf Projecten/MarkdownTaskManager/EPIC-TEST
```

---

## 🔍 Structuur Verificatie

Bekijk de nieuwe file structuur:

```bash
find Projecten/MarkdownTaskManager -name "*.md" | sort
```

**Verwachte output:**
```
Projecten/MarkdownTaskManager/EPIC-001/epic.md
Projecten/MarkdownTaskManager/EPIC-001/FEATURE-001/feature.md
Projecten/MarkdownTaskManager/EPIC-001/FEATURE-001/STORY-001/story.md
Projecten/MarkdownTaskManager/EPIC-001/FEATURE-001/STORY-001/TASK-001.md
Projecten/MarkdownTaskManager/EPIC-001/FEATURE-001/STORY-001/TASK-002.md
...
```

✅ Geen `features/`, `stories/`, `tasks/` folders!

---

## 📝 Markdown Links Verificatie

Controleer of links correct zijn aangepast:

```bash
grep -r "\[.*\](.*\.md)" Projecten/MarkdownTaskManager | head -10
```

**Verwachte links:**
- `[FEATURE-001](FEATURE-001/feature.md)` ✅
- `[STORY-001](STORY-001/story.md)` ✅
- `[TASK-001](TASK-001.md)` ✅

**NIET meer:**
- `[FEATURE-001](features/FEATURE-001/feature.md)` ❌
- `[STORY-001](stories/STORY-001/story.md)` ❌

---

## 🎯 Interactieve Test

### Stap 1: Start File Watcher
```bash
python3 backend/app/sync/test_watcher_live.py
```

### Stap 2: Open een ander terminal venster
```bash
# Pas een epic aan
nano Projecten/MarkdownTaskManager/EPIC-001/epic.md

# Voeg bijvoorbeeld een extra tag toe
# Sla op (Ctrl+O, Enter, Ctrl+X)
```

### Stap 3: Kijk naar het watcher terminal
Je zou moeten zien:
```
======================================================================
🔄 SYNC TRIGGERED!
======================================================================
File change detected - would sync to database now
✅ Sync complete!
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'watchdog'"
```bash
pip install watchdog --break-system-packages
# of
uv pip install watchdog
```

### "FileNotFoundError: Markdown directory not found"
Controleer of de directory bestaat:
```bash
ls -la Projecten/MarkdownTaskManager/
```

### Parser vindt geen epics
Controleer de structuur:
```bash
ls -la Projecten/MarkdownTaskManager/
# Zou EPIC-001, EPIC-002, EPIC-003 moeten laten zien
```

---

## ✅ Verwachte Test Resultaten

Alle tests zouden moeten slagen:

- ✅ Roundtrip test: **PASSED**
- ✅ Sync engine test: **COMPLETE**
- ✅ File watcher: Detecteert wijzigingen
- ✅ Parser: Leest 3 epics, 3 features, 3 stories, 4 tasks
- ✅ Generator: Maakt correcte markdown files
- ✅ Links: Geen intermediate folders

---

## 🚀 Volgende Stappen

Na succesvolle tests:

1. **Database integratie**: Definieer SQLAlchemy models
2. **API endpoints**: Integreer met FastAPI
3. **Production deployment**: Docker, monitoring, etc.

---

**Vragen?** Vraag gerust!
