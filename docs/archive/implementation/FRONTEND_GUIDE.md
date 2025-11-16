# Frontend Gebruikershandleiding

## 🎨 Hoe te gebruiken

### Stap 1: Start de Backend
De backend moet draaien op poort 8000:

```bash
# Draait al in de achtergrond!
# Check: http://localhost:8000/api/docs
```

### Stap 2: Open de Frontend
Open in je browser:

```bash
file:///home/eddie/Projects/MarkdownTaskManager/frontend/index.html
```

Of via een lokale webserver:

```bash
# Python webserver (aanbevolen vanwege CORS)
cd /home/eddie/Projects/MarkdownTaskManager
python3 -m http.server 8080

# Open: http://localhost:8080/frontend/index.html
```

### Stap 3: Project Laden
1. Klik op **"🔄 Project Laden"**
2. De frontend laadt alle epics, features, stories en tasks via de API
3. Je ziet de volledige hiërarchie in de sidebar

### Stap 4: Navigeren
- **Klik op een item** in de sidebar om details te zien
- **Bekijk children** (features, stories, tasks) in cards
- **Zie metadata** zoals status, priority, story points

### Stap 5: Bewerken
- Klik op **"✏️ Bewerk in Markdown"**
- Je krijgt het bestandspad te zien
- Open het bestand in je editor
- **File watcher** detecteert wijzigingen automatisch!

---

## 📊 Wat Kun Je Zien

### Epic View
- 📊 Epic titel en ID
- Status, Priority, Phase
- Business Value
- Story Points (total en completed)
- Alle features als cards

### Feature View
- 🎯 Feature titel en ID
- Status, Priority
- Story Points
- Alle stories als cards

### Story View
- 📝 Story titel en ID
- Status
- Story Points
- Estimated Hours
- Alle tasks als cards

### Task View
- ✓ Task titel en ID
- Status
- Beschrijving

---

## 🔄 Live Sync Workflow

### Met File Watcher (Aanbevolen)
```bash
# Terminal 1: Start file watcher
python3 backend/app/sync/test_watcher_live.py

# Terminal 2: Open frontend
# Werk in je markdown files

# Terminal 3 (optioneel): Bekijk backend
# Je backend draait al!
```

### Workflow:
1. Open een markdown bestand
2. Maak wijzigingen en sla op
3. File watcher detecteert wijziging (Terminal 1)
4. Sync wordt getriggerd (debounce 2s)
5. Herlaad frontend met F5
6. Zie je wijzigingen!

---

## 🎯 Praktisch Voorbeeld

### Nieuwe Story Toevoegen

1. **In Frontend**: Klik op EPIC-001 → FEATURE-001
2. **Zie**: Huidige stories in cards
3. **Edit**: Open `Projecten/MarkdownTaskManager/EPIC-001/FEATURE-001/story.md`
4. **Voeg toe**: Nieuwe story sectie
5. **Save**: File watcher triggert sync
6. **Reload**: F5 in browser
7. **Result**: Nieuwe story verschijnt!

### Status Wijzigen

1. **In Frontend**: Klik op een story
2. **Zie**: Status = PLANNED
3. **Edit**: Open het story.md bestand
4. **Change**: `status: PLANNED` → `status: IN_PROGRESS`
5. **Save**: File watcher triggert
6. **Reload**: Zie nieuwe status!

---

## 🚀 Advanced Features

### Manual Sync
```bash
# Trigger sync from button
Klik: "💾 Sync naar Database"

# Or via API
curl -X POST http://localhost:8000/api/sync/markdown-to-db
```

### API Endpoints

#### Project Data
```bash
GET http://localhost:8000/api/project/
GET http://localhost:8000/api/project/epics
GET http://localhost:8000/api/project/epic/EPIC-001
GET http://localhost:8000/api/project/stats
```

#### Sync
```bash
POST http://localhost:8000/api/sync/markdown-to-db
POST http://localhost:8000/api/sync/db-to-markdown
POST http://localhost:8000/api/sync/watcher/start
POST http://localhost:8000/api/sync/watcher/stop
GET  http://localhost:8000/api/sync/watcher/status
```

---

## 📁 File Structuur Begrijpen

### Wat je ziet in frontend:
```
📊 EPIC-001: Payment Integration
  🎯 FEATURE-001: Stripe API Integration
    📝 STORY-001: Setup Stripe SDK
      ✓ TASK-001: Install stripe package
      ✓ TASK-002: Configure API keys
```

### Wat er op disk staat:
```
Projecten/MarkdownTaskManager/
└── EPIC-001/
    ├── epic.md
    └── FEATURE-001/
        ├── feature.md
        └── STORY-001/
            ├── story.md
            ├── TASK-001.md
            └── TASK-002.md
```

✅ **Geen intermediate folders** (features/, stories/, tasks/)!

---

## 🐛 Troubleshooting

### Frontend toont geen data
```bash
# Check backend
curl http://localhost:8000/api/health

# Check API
curl http://localhost:8000/api/project/

# Check console in browser (F12)
```

### CORS Errors
```bash
# Use local webserver instead of file://
python3 -m http.server 8080
# Then: http://localhost:8080/frontend/index.html
```

### Wijzigingen niet zichtbaar
```bash
# 1. Check file watcher draait
ps aux | grep test_watcher

# 2. Manual sync
curl -X POST http://localhost:8000/api/sync/markdown-to-db

# 3. Hard reload browser
Ctrl+Shift+R (or Cmd+Shift+R on Mac)
```

---

## 🎨 Wat komt er nog

### Geplande Features
- [ ] Inline editing in frontend (direct in browser bewerken)
- [ ] Drag & drop om volgorde te wijzigen
- [ ] Bulk operations (status van meerdere items tegelijk)
- [ ] Zoekfunctie
- [ ] Filters (by status, priority, owner)
- [ ] Gantt chart / timeline view
- [ ] Sprint board view
- [ ] Real-time sync (WebSockets)

---

## 📝 Tips & Tricks

### Sneltoetsen (in je editor)
- Gebruik een markdown editor met preview
- VS Code extensions: Markdown All in One
- Vim: markdown-preview.nvim

### Best Practices
- Kleine, frequente wijzigingen
- Test altijd met F5 reload
- Check file watcher output
- Gebruik git voor backup

### Performance
- Frontend laadt momenteel alle data
- Voor grote projecten: pagination toevoegen
- Cache data in browser localStorage

---

**Veel succes met je Markdown Task Manager! 🚀**
