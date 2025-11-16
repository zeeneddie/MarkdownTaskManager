# Project Manager - Complete Project Documentation

Een volledig functioneel hierarchisch project management systeem gebaseerd op markdown bestanden en lokale folders. Geschikt voor Agile/Scrum development met support voor Epics, Features, Stories, Tasks, Sprints, en volledige CRUD+Move operaties.

## 📋 Overzicht

**Project Manager** (`project-manager.html`) is een standalone web application voor hierarchische project planning met vier niveaus:

```
Epic (Groot initiatief, maanden)
  └── Feature (Capability, weken)
       └── Story (User story, dagen)
            └── Task (Implementatie stap, uren)
```

### Kernfunctionaliteit:
- ✅ **Hierarchische navigatie**: Drill-down door Epic → Feature → Story → Task
- ✅ **Sprint planning**: Filter en plan stories per sprint
- ✅ **CRUD operations**: Create, Read, Update, Delete met undo
- ✅ **Move functionality**: Verplaats items tussen parents
- ✅ **Auto-aggregation**: Story Points rollen automatisch op
- ✅ **Git-friendly**: Plain text markdown files

---

## 🚀 Quick Start

### 1. Open Application
```bash
# Chrome/Edge required (File System Access API)
open project-manager.html
```

### 2. Load Project
1. Click "📂 Load Project Folder"
2. Select project root (e.g., `example-project/`)
3. Grant file permissions
4. View hierarchical structure

### 3. Navigate
- Click Epic → See Features
- Click Feature → See Stories
- Click Story → See Tasks
- Use breadcrumbs to go back

### 4. Create/Edit/Delete
- **Create**: Click "+ New [Type]" button
- **Edit**: Click ✏️ on any card
- **Delete**: In edit modal, click "🗑️ Delete" (soft delete)
- **Move**: In edit modal, click "↔️ Move"
- **Restore**: Click "↶ Restore Deleted" button

---

## 📊 Feature Overview

### ✅ Volledig Geïmplementeerd (V2.0)

#### 1. Hierarchische Navigatie
- **4 Levels**: Epic → Feature → Story → Task
- **Breadcrumb trail**: Home > Epic > Feature > Story
- **On-demand loading**: Lazy loading van children
- **Context awareness**: Breadcrumbs voor parent context

#### 2. Sprint Support
- **Sprint field**: In story metadata
- **Sprint filter dropdown**: Filter stories per sprint
- **Filter opties**:
  - All Sprints
  - Current Sprint (meest recente)
  - No Sprint Assigned
  - Dynamische sprint list
- **Real-time filtering**: Instant UI update

#### 3. Full CRUD Operations

**Create**:
- Auto-generated IDs (EPIC-001, FEATURE-001, etc.)
- Folder structure automatisch aangemaakt
- Default waarden voor nieuwe items
- Breadcrumb context voor correct path

**Read**:
- Multi-file folder structure parsing
- Markdown metadata extraction
- Hierarchical relationship tracking
- On-demand loading

**Update**:
- Full edit modal met alle velden
- Dynamic form fields per type
- Auto-aggregation na save
- Instant UI refresh

**Delete** (Soft Delete):
- Move naar `.deleted/` folder met timestamp
- Recursive delete voor folders
- Confirmation dialogs
- Auto-aggregation na delete

#### 4. Soft Delete + Undo
- **Timestamp naming**: `ITEM-001-name_2025-11-12T14-30-45`
- **Restore modal**: Lijst van deleted items
- **One-click restore**: Herstel met confirmatie
- **Overwrite protection**: Vraag confirmatie bij conflict
- **Hierarchical .deleted folders**:
  - `epics/.deleted/`
  - `epics/EPIC-XXX/features/.deleted/`
  - `epics/EPIC-XXX/features/FEATURE-XXX/stories/.deleted/`
  - `epics/EPIC-XXX/.../tasks/.deleted/`

#### 5. Move Functionality
- **Move tasks**: Naar andere stories
- **Move stories**: Naar andere features
- **Move features**: Naar andere epics
- **Cross-epic moves**: Kan over epic grenzen
- **Destination browser**: Modal met lijst van targets
- **Path display**: Volledige path van destination
- **Conflict handling**: Overwrite confirmation

#### 6. Auto-Aggregation
- **Story Points**: Optellen van children naar parent
- **Progress**: Automatische percentage berekening
- **Cascade updates**:
  - Story wijzigt → Feature updates → Epic updates
  - Complete cascade bij delete/move
- **Real-time**: Direct na save/create

#### 7. Status & Priority Management
- **Status dropdown**: PLANNED, IN_PROGRESS, TESTING, COMPLETED
- **Priority levels**: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW
- **Visual indicators**: Color-coded badges
- **Configurable**: Via project.md columns

#### 8. Metadata Tracking
- **Dates**: Created, Started, Target, Completed
- **Ownership**: Owner (Epic/Feature), Assigned (Story/Task)
- **Story Points**: SP field voor Stories, aggregated totals
- **Hours**: Hour estimates voor Tasks
- **Phase**: Epic lifecycle phase

---

## 📁 File Structure

```
example-project/
├── project.md                # Project metadata
├── epics/
│   └── EPIC-001-assessment/
│       ├── epic.md          # Epic metadata + aggregated totals
│       ├── .deleted/        # Deleted features with timestamp
│       └── features/
│           └── FEATURE-001-analysis/
│               ├── feature.md
│               ├── .deleted/       # Deleted stories
│               └── stories/
│                   └── STORY-001-metrics/
│                       ├── story.md
│                       ├── .deleted/      # Deleted tasks
│                       └── tasks/
│                           ├── TASK-001.md
│                           └── TASK-002.md
```

### Deleted Items:
```
.deleted/
├── EPIC-002-old-initiative_2025-11-12T14-30-45/
├── FEATURE-005-deprecated_2025-11-11T09-15-22/
└── STORY-010-obsolete_2025-11-10T16-45-30/
```

---

## 🎨 Data Model

### Epic Schema
```markdown
# EPIC-001 | Technical Assessment & Planning

**Parent**: `../../project.md`
**Type**: Epic
**Priority**: 🔴 CRITICAL
**Status**: IN_PROGRESS
**Owner**: @eddie
**Phase**: Assessment

## Story Points
**Total**: 34 SP
**Completed**: 13 SP
**Progress**: 38%

## Dates
**Created**: 2025-01-15
**Started**: 2025-01-20
**Target**: 2025-03-01

## Description
Initial technical assessment phase to evaluate codebase...

## Goals
- Assess current state
- Identify pain points
- Create improvement roadmap
```

### Feature Schema
```markdown
# FEATURE-001 | Codebase Quality Analysis

**Parent**: `../../epic.md`
**Type**: Feature
**Priority**: 🔴 CRITICAL
**Status**: IN_PROGRESS
**Owner**: @eddie

## Story Points
**Total**: 13 SP
**Completed**: 5 SP
**Progress**: 38%

## Dates
**Created**: 2025-01-20
**Started**: 2025-01-22
**Target**: 2025-02-15

## Description
Comprehensive analysis of codebase quality metrics...
```

### Story Schema
```markdown
# STORY-001 | Analyze code metrics and complexity

**Parent**: `../../feature.md`
**Type**: Story
**Priority**: 🟠 HIGH
**Status**: IN_PROGRESS
**Assigned**: @eddie
**Sprint**: Sprint-2025-11-15

## Story Points
**SP**: 5

## Dates
**Created**: 2025-01-22
**Started**: 2025-01-25
**Target**: 2025-02-01

## Description
Measure code complexity, technical debt, and quality metrics...

## Acceptance Criteria
- [ ] Metrics dashboard created
- [ ] Key metrics identified and documented
- [ ] Baseline measurements recorded
```

### Task Schema
```markdown
# TASK-001 | Setup metrics collection tooling

**Parent**: `../story.md`
**Type**: Task
**Priority**: 🔴 CRITICAL
**Status**: IN_PROGRESS
**Assigned**: @eddie

## Effort
**Hours**: 4h

## Dates
**Created**: 2025-01-25
**Started**: 2025-01-25

## Description
Configure automated tooling for code quality metrics collection...

## Steps
- Install SonarQube
- Configure eslint with complexity rules
- Setup automated reporting
```

---

## 🎯 Workflow Examples

### Sprint Planning Workflow
```
1. Create Epic "User Management" (EPIC-002)
2. Create Features:
   - FEATURE-003: Authentication
   - FEATURE-004: Authorization
   - FEATURE-005: User profiles

3. Create Stories in each feature:
   - STORY-010: Login flow (5 SP)
   - STORY-011: OAuth integration (8 SP)
   - STORY-012: Password reset (3 SP)
   - etc.

4. Assign to Sprint:
   - Edit each story
   - Set Sprint: "Sprint-2025-11-15"
   - Set Assigned: "@alice"

5. Filter by Sprint:
   - Navigate to stories level
   - Sprint filter: "Sprint-2025-11-15"
   - View: 3 stories, 16 SP total

6. Track Progress:
   - Mark stories as IN_PROGRESS
   - Complete tasks
   - Auto-aggregation updates SP totals
   - Sprint velocity tracked
```

### Task Reorganization Workflow
```
1. Realize TASK-005 belongs to different story
2. Navigate to current story
3. Edit TASK-005
4. Click "↔️ Move"
5. See list of other stories
6. Select "STORY-015 | API Integration"
7. Confirm move
8. Task relocates:
   - From: .../STORY-010/tasks/
   - To: .../STORY-015/tasks/
9. Both stories auto-aggregate
```

### Accidental Delete Recovery
```
1. Delete STORY-020 by mistake
2. Realize error
3. Click "↶ Restore Deleted"
4. See modal with deleted items:
   - STORY-020-api-refactor_2025-11-12T15-30-00
5. Click "↶ Restore"
6. Confirmation: "Restore STORY-020?"
7. Story restored with all tasks intact
8. .deleted/ entry removed
```

---

## 🏗️ Architecture

### File System Access API
```javascript
// Directory access
const directoryHandle = await window.showDirectoryPicker();

// Read epic
const epicsDir = await directoryHandle.getDirectoryHandle('epics');
const epicDir = await epicsDir.getDirectoryHandle('EPIC-001-assessment');
const epicFile = await epicDir.getFileHandle('epic.md');
const content = await (await epicFile.getFile()).text();

// Write epic
const writable = await epicFile.createWritable();
await writable.write(serializeEpic(epic));
await writable.close();

// Create folder structure
const featuresDir = await epicDir.getDirectoryHandle('features', { create: true });
const featureDir = await featuresDir.getDirectoryHandle('FEATURE-001-analysis', { create: true });
```

### State Management
```javascript
// Global state
let directoryHandle = null;       // File system access
let items = [];                   // Current level items
let breadcrumbs = [];             // Navigation context
let currentViewLevel = 'epic';    // epic|feature|story|task
let currentSprintFilter = '';     // Sprint filter state
let config = {};                  // Project configuration
```

### Breadcrumb Navigation
```javascript
const breadcrumbs = [
    { level: 'epic', id: 'EPIC-001', folderName: 'EPIC-001-assessment', title: 'Assessment' },
    { level: 'feature', id: 'FEATURE-001', folderName: 'FEATURE-001-analysis', title: 'Analysis' },
    { level: 'story', id: 'STORY-001', folderName: 'STORY-001-metrics', title: 'Metrics' }
];

// Navigate to story tasks
await navigateToLevel('task', storyItem);
// Breadcrumbs track full path for parent resolution
```

### Auto-Aggregation Logic
```javascript
async function aggregateToFeature(story) {
    // Find parent feature from breadcrumbs
    const featureCrumb = breadcrumbs.find(c => c.level === 'feature');

    // Load all stories in feature
    const stories = await loadStoriesInFeature(featureCrumb);

    // Calculate totals
    feature.spTotal = stories.reduce((sum, s) => sum + s.sp, 0);
    feature.spCompleted = stories
        .filter(s => s.status === 'completed')
        .reduce((sum, s) => sum + s.sp, 0);
    feature.progress = feature.spTotal > 0
        ? Math.round((feature.spCompleted / feature.spTotal) * 100)
        : 0;

    await saveFeature(feature);

    // Cascade to epic
    await aggregateToEpic(feature);
}
```

---

## 🔄 Integration met Kanban Board

Zie **INTEGRATION_PROPOSAL.md** voor volledige integratie design.

### Huidige Status:
- ❌ **Niet geïntegreerd**: project-manager.html en task-manager.html zijn aparte systemen
- ❌ **Geen data sharing**: Geen automatische sync
- ❌ **Geen parent links**: Kanban tasks refereren niet naar project stories

### Voorgestelde Integratie:
1. **Parent Story Link**: Kanban tasks → Project stories
2. **Sprint filter in Kanban**: Filter kanban op active sprint
3. **Auto-push**: Stories in sprint → Automatic kanban task creation
4. **Bidirectional sync**: Updates in kanban → Reflect in project
5. **Unified dashboard**: Combined view van beide systemen

### Implementation Priority:
**Phase 3** in roadmap (MEDIUM priority, 1 week effort)

---

## 📈 Development Stats

### Version History:
- **V1.0** (2025-11-12): Initial hierarchical navigation + CRUD
- **V1.1** (2025-11-12): Delete functionality
- **V2.0** (2025-11-12): Sprint support + Soft delete/undo + Move

### Code Statistics:
```
Total Lines of Code:      ~5,750
├── HTML:                 ~920
├── CSS:                  ~280
└── JavaScript:           ~4,550

Functions:                100+
UI Modals:                3 (Edit, Restore, Move)
Development Time:         3 sessies
Documentation Lines:      ~3,200
```

### Feature Breakdown:
| Feature | Lines | Functions | Status |
|---------|-------|-----------|--------|
| Hierarchical Navigation | ~800 | 15 | ✅ V1.0 |
| CRUD Operations | ~1,200 | 25 | ✅ V1.0 |
| Auto-Aggregation | ~400 | 8 | ✅ V1.0 |
| Delete | ~210 | 4 | ✅ V1.1 |
| Sprint Support | ~120 | 3 | ✅ V2.0 |
| Soft Delete + Undo | ~350 | 6 | ✅ V2.0 |
| Move Functionality | ~370 | 5 | ✅ V2.0 |

---

## 🔮 Roadmap

### Phase 1: Sprint Enhancements (HIGH Priority) 🎯
**Estimated**: 2 weeks

- [ ] Sprint metadata files (`sprints/SPRINT-XXX/sprint.md`)
- [ ] Sprint start/end dates
- [ ] Sprint goal definition
- [ ] Team capacity planning
- [ ] Sprint board view (stories kanban)
- [ ] Drag-drop stories to sprint
- [ ] Burndown chart visualization
- [ ] Velocity tracking

**Documentation**: INTEGRATION_PROPOSAL.md (lines 190-225)

### Phase 2: Many-to-Many Relationships (MEDIUM Priority) 📋
**Estimated**: 2 weeks

- [ ] Shared tasks (1 task → N stories)
- [ ] Shared stories (1 story → N features)
- [ ] Primary + additional parents UI
- [ ] Dependency graph (vis.js/D3)
- [ ] Multi-parent aggregation

**Documentation**: MANY_TO_MANY_RELATIONSHIPS.md

### Phase 3: Kanban Integration (MEDIUM Priority) 🔄
**Estimated**: 1 week

- [ ] Link kanban tasks → project stories
- [ ] Parent story in kanban cards
- [ ] Sprint filter in kanban
- [ ] Bidirectional sync
- [ ] Auto-push to kanban on sprint start

**Documentation**: INTEGRATION_PROPOSAL.md (lines 100-112)

### Phase 4: Dependencies & Libraries (NEW) 🔗
**Estimated**: 1 week

- [ ] Library/dependency field
- [ ] Conditional dependencies
- [ ] Dependency visualization
- [ ] Impact analysis
- [ ] Dependency graph

**Documentation**: (To be created)

### Phase 5: Dashboard & Reporting (LOW Priority) 📊
**Estimated**: 2 weeks

- [ ] Unified dashboard
- [ ] Active sprint widget
- [ ] Team velocity chart
- [ ] Burndown charts
- [ ] Export to Excel/PDF

---

## ⚠️ Known Limitations

### Browser Compatibility:
- ❌ **Chrome/Edge 86+ only**: File System Access API
- ❌ **No Firefox/Safari**: API not available
- ❌ **No mobile**: Not optimized for touch

### Functional Limitations:
- ❌ **No undo for move**: Only delete has undo
- ❌ **No bulk operations**: Single item at a time
- ❌ **No search**: No global search (yet)
- ❌ **No epic move**: No parent for epic
- ❌ **No real-time collaboration**: No multi-user
- ❌ **No history**: Use Git for version history

### Data Limitations:
- ⚠️ **Single parent only**: No shared tasks (yet)
- ⚠️ **Manual sprint creation**: No sprint files (yet)
- ⚠️ **No dependencies UI**: Metadata exists, no UI
- ⚠️ **No library tracking**: No conditional dependencies (yet)

### Performance:
- ⚠️ **Large projects**: 100+ items can be slow
- ⚠️ **No pagination**: Loads all items at once

---

## 📚 Documentation Files

| File | Description | Lines |
|------|-------------|-------|
| **PROJECT_MANAGER_README.md** | This file - Complete overview | ~600 |
| **INTEGRATION_PROPOSAL.md** | Sprint/Kanban integration design | ~477 |
| **MANY_TO_MANY_RELATIONSHIPS.md** | Shared tasks/stories guide | ~600 |
| **SPRINT_UNDO_MOVE_IMPLEMENTATION.md** | V2.0 implementation | ~500 |
| **DELETE_FEATURE.md** | Delete functionality docs | ~323 |
| **IMPLEMENTATION_COMPLETE.md** | V1.0 summary | ~330 |
| **EDIT_FEATURE_TEST.md** | Testing guide | ~203 |

**Total**: ~3,000+ lines of documentation

---

## 🛠️ Development

### Running Locally:
```bash
# Option 1: Direct open
open project-manager.html

# Option 2: Local server
python -m http.server 8000
# http://localhost:8000/project-manager.html
```

### Debugging:
```javascript
// Console logs enabled throughout
console.log(`Loading ${currentViewLevel} items...`);
console.log(`Saving ${item.type}: ${item.id}`);
console.log(`✓ ${item.type} saved successfully`);

// Open DevTools (F12) → Console tab
```

### Adding Features:
1. Update schema in serializer/parser
2. Add UI fields in edit modal
3. Update renderHierarchy() for display
4. Test with example-project
5. Document in .md file

---

## 🤝 Related Files

- **task-manager.html**: Kanban board application
- **kanban.md**: Daily task management
- **archive.md**: Completed tasks archive
- **AI_WORKFLOW.md**: Guidelines for AI assistants

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Built with vanilla JavaScript (no frameworks!)
- Uses browser-native File System Access API
- Inspired by Jira, Linear, and Notion
- Designed for local-first, Git-friendly workflow

---

**Last Updated**: 2025-11-12
**Version**: 2.0
**Status**: ✅ Production Ready
**Next Release**: Sprint Enhancements (Planned Q1 2026)

🚀 **Ready to manage complex projects hierarchically!**
