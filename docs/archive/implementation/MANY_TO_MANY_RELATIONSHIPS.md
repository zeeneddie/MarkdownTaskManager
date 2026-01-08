# Many-to-Many Relationships - Implementation Guide

## 🎯 Probleem

In de huidige implementatie is er een **strikte hiërarchie**:
```
Epic → Feature → Story → Task
```

Maar in de praktijk:
- **1 Task kan bijdragen aan meerdere Stories** (gedeelde infrastructuur, shared componenten)
- **1 Story kan bijdragen aan meerdere Features** (cross-cutting concerns)
- **1 Feature kan bijdragen aan meerdere Epics** (large initiatives)

## 📊 Voorbeelden

### Voorbeeld 1: Shared Task
```
TASK-001: "Setup database schema"

Nodig voor:
- STORY-001: User authentication
- STORY-002: User profile management
- STORY-005: Admin dashboard

Als TASK-001 completed is:
→ Alle 3 stories kunnen vooruit
→ Progress van alle 3 stories moet updaten
```

### Voorbeeld 2: Shared Story
```
STORY-010: "API rate limiting"

Nodig voor:
- FEATURE-001: Public API
- FEATURE-002: Mobile app backend
- FEATURE-003: Third-party integrations

Als STORY-010 completed is:
→ Alle 3 features kunnen vooruit
→ Progress van alle 3 features moet updaten
```

---

## 🔧 Implementatie Opties

### Optie 1: Reference-Based Model (Aanbevolen) ⭐

#### Data Model:

**Task met meerdere parents:**
```markdown
# TASK-001 | Setup database schema

**Primary Parent**: STORY-001
**Additional Parents**: STORY-002, STORY-005
**Type**: Task
**Status**: IN_PROGRESS

## Parent Stories
- [STORY-001](../../STORY-001-auth/story.md) - User authentication
- [STORY-002](../../STORY-002-profile/story.md) - User profile
- [STORY-005](../../STORY-005-admin/story.md) - Admin dashboard

## Description
This task provides database infrastructure needed by multiple stories.
```

**Story met meerdere parents:**
```markdown
# STORY-010 | API rate limiting

**Primary Parent**: FEATURE-001
**Additional Parents**: FEATURE-002, FEATURE-003
**Type**: Story
**Status**: COMPLETED

## Parent Features
- [FEATURE-001](../../FEATURE-001-api/feature.md) - Public API
- [FEATURE-002](../../FEATURE-002-mobile/feature.md) - Mobile backend
- [FEATURE-003](../../FEATURE-003-integrations/feature.md) - Integrations

## Story Points
**SP**: 8

## Description
Implement rate limiting to protect all API endpoints.
```

#### UI Changes:

**1. In Task Card:**
```
┌─────────────────────────────────────────────┐
│ TASK-001 | Setup database                   │
│                                             │
│ Status: IN_PROGRESS    Priority: HIGH      │
│                                             │
│ 📖 Parent Stories (3):                     │
│   • STORY-001: Auth                        │
│   • STORY-002: Profile                     │
│   • STORY-005: Admin                       │
│                                             │
│ This task contributes to 3 stories         │
└─────────────────────────────────────────────┘
```

**2. In Edit Modal:**
```
┌─────────────────────────────────────────────┐
│ Edit Task                                   │
│                                             │
│ Title: [Setup database schema           ]  │
│                                             │
│ Primary Parent Story:                       │
│ [STORY-001 ▼]                              │
│                                             │
│ Additional Parent Stories:                  │
│ [+ Add Parent Story]                        │
│   × STORY-002 | User profile               │
│   × STORY-005 | Admin dashboard            │
│                                             │
│ When this task completes:                   │
│ → All 3 parent stories will be updated     │
└─────────────────────────────────────────────┘
```

#### Aggregation Logic:

**Voor Tasks met meerdere parents:**
```javascript
async function completeTask(task) {
    task.status = 'completed';

    // Update ALL parent stories
    for (const parentId of task.parentStories) {
        const story = await findStoryById(parentId);
        await aggregateToStory(story);
    }

    // Primary parent's feature aggregation
    const primaryStory = await findStoryById(task.primaryParent);
    await aggregateToFeature(primaryStory);
}
```

**SP Distribution Options:**

**Option A: Shared SP (Split)**
```
STORY-001: 8 SP total
├── TASK-001 (shared): 2 SP (contributes 2 to this story)
├── TASK-002 (exclusive): 3 SP
└── TASK-003 (exclusive): 3 SP

STORY-002: 5 SP total
├── TASK-001 (shared): 2 SP (contributes 2 to this story)
└── TASK-004 (exclusive): 3 SP

TASK-001 total hours: 8h
TASK-001 SP per story: 2 (can be configured per relationship)
```

**Option B: Full SP (Duplicate counting)**
```
STORY-001: 13 SP total
├── TASK-001 (shared): 5 SP (full weight)
├── TASK-002: 3 SP
└── TASK-003: 5 SP

STORY-002: 8 SP total
├── TASK-001 (shared): 5 SP (full weight)
└── TASK-004: 3 SP

When TASK-001 completes:
→ Both STORY-001 and STORY-002 get 5 SP completed
```

**Aanbeveling**: Option B (Full SP) is simpeler en eerlijker - als task blocking is voor story, dan moet hele SP count meegenomen worden.

---

### Optie 2: Reference Files (Symlinks in Filesystem)

#### Folder Structure:
```
epics/
  EPIC-001-assessment/
    features/
      FEATURE-001-codebase/
        stories/
          STORY-001-auth/
            tasks/
              TASK-001.md          ← Primary location
              TASK-002.md
          STORY-002-profile/
            tasks/
              TASK-001-ref.md      ← Reference naar TASK-001
              TASK-003.md
```

#### Reference File Format:
```markdown
# REF → TASK-001 | Setup database schema

**Type**: Task Reference
**Primary Location**: `../../../STORY-001-auth/tasks/TASK-001.md`
**Relationship**: Shared Infrastructure

## Why This Task is Needed
This story requires database access provided by TASK-001.

## Status
Check primary location for current status: [View TASK-001](../../../STORY-001-auth/tasks/TASK-001.md)
```

#### Implementation:

**Parser herkennen van reference files:**
```javascript
function parseTaskFile(content) {
    const lines = content.split('\n');
    const firstLine = lines[0];

    // Check if reference file
    if (firstLine.includes('# REF →')) {
        return {
            type: 'task-reference',
            isReference: true,
            originalId: extractIdFromRef(firstLine),
            primaryLocation: extractMetadata(content, 'Primary Location'),
            // ... other fields
        };
    }

    // Normal task parsing
    return {
        type: 'task',
        isReference: false,
        // ... normal task fields
    };
}
```

**UI rendering van references:**
```javascript
function renderTaskCard(task) {
    if (task.isReference) {
        return `
            <div class="task-card reference-card">
                <div class="reference-indicator">🔗 Shared Task</div>
                <div class="task-title">${task.title}</div>
                <div class="reference-info">
                    Defined in: ${task.primaryLocation}
                    <button onclick="navigateToOriginal('${task.primaryLocation}')">
                        View Original →
                    </button>
                </div>
            </div>
        `;
    }

    // Normal task rendering
    return renderNormalTask(task);
}
```

#### Voordelen & Nadelen:

**✅ Voordelen:**
- Fysieke representatie in filesystem
- Duidelijk verschil tussen primary en reference
- Geen duplicate data (single source of truth)

**❌ Nadelen:**
- Meer bestanden (1 primary + N references)
- Complexere parsing logic
- References kunnen out-of-sync raken
- Moeilijker te synchroniseren

---

### Optie 3: Junction Table (Database-style)

Nieuwe file: `relationships.md` in project root:

```markdown
# Project Relationships

## Task → Story Relationships

| Task ID | Story IDs | Contribution Type |
|---------|-----------|-------------------|
| TASK-001 | STORY-001, STORY-002, STORY-005 | Shared Infrastructure |
| TASK-007 | STORY-003, STORY-004 | Shared Component |

## Story → Feature Relationships

| Story ID | Feature IDs | Contribution Type |
|----------|-------------|-------------------|
| STORY-010 | FEATURE-001, FEATURE-002 | Cross-cutting |
| STORY-015 | FEATURE-003, FEATURE-004, FEATURE-005 | Foundation |

## Notes
- Primary parent is always listed first
- Contribution type helps understand the relationship nature
```

#### Implementation:

**Load relationships bij app startup:**
```javascript
let relationships = {};

async function loadRelationships() {
    const file = await directoryHandle.getFileHandle('relationships.md');
    const content = await file.text();

    relationships = parseRelationships(content);
    // {
    //   'TASK-001': { parents: ['STORY-001', 'STORY-002', 'STORY-005'], type: 'Shared' },
    //   'STORY-010': { parents: ['FEATURE-001', 'FEATURE-002'], type: 'Cross-cutting' }
    // }
}

function getParentsForItem(itemId) {
    return relationships[itemId]?.parents || [];
}
```

**UI voor managing relationships:**
```
┌─────────────────────────────────────────────┐
│ Manage Relationships                        │
│                                             │
│ TASK-001 | Setup database                   │
│                                             │
│ Parent Stories:                             │
│ • STORY-001 (Primary) [Remove]             │
│ • STORY-002          [Remove]              │
│ • STORY-005          [Remove]              │
│                                             │
│ [+ Add Parent Story ▼]                     │
│                                             │
│ [Save]  [Cancel]                           │
└─────────────────────────────────────────────┘
```

**✅ Voordelen:**
- Centraal overzicht van alle relaties
- Makkelijk te query'en
- Simpele data structure

**❌ Nadelen:**
- Single point of failure (als relationships.md corrupt is)
- Kan out-of-sync raken met items
- Niet zichtbaar in individual item files

---

## 🎨 UI/UX Changes Needed

### 1. Task Card Enhancements
```javascript
function createHierarchyCard(item) {
    // ... existing code

    // Add parent relationships indicator
    if (item.parentStories && item.parentStories.length > 1) {
        cardHTML += `
            <div class="shared-indicator">
                🔗 Shared across ${item.parentStories.length} stories
            </div>
        `;
    }
}
```

### 2. Edit Modal: Parent Selector
```html
<div class="form-group" id="parentStoriesField">
    <label>Parent Stories</label>

    <!-- Primary parent (required) -->
    <div>
        <label style="font-size: 0.9rem;">Primary Parent:</label>
        <select id="primaryParentStory">
            <option value="STORY-001">STORY-001 | User authentication</option>
            <option value="STORY-002">STORY-002 | User profile</option>
        </select>
    </div>

    <!-- Additional parents (optional) -->
    <div style="margin-top: 1rem;">
        <label style="font-size: 0.9rem;">Additional Parents:</label>
        <div id="additionalParentsList">
            <div class="parent-item">
                <span>STORY-002 | User profile</span>
                <button onclick="removeParent('STORY-002')">×</button>
            </div>
        </div>
        <button class="btn btn-secondary" onclick="addParentStory()">+ Add Parent Story</button>
    </div>
</div>
```

### 3. Dependency Graph View (Nieuw)
```
Visualisatie van relationships:

        EPIC-001
           |
      FEATURE-001
        /    \
       /      \
  STORY-001  STORY-002
       \      /
        \    /
       TASK-001

Labels:
→ TASK-001 is shared tussen STORY-001 en STORY-002
→ Completing TASK-001 updates both stories
```

**Implementation met vis.js of D3.js:**
```javascript
function renderDependencyGraph() {
    const nodes = [];
    const edges = [];

    // Add all items as nodes
    items.forEach(item => {
        nodes.push({
            id: item.id,
            label: item.id,
            title: item.title,
            level: item.type
        });

        // Add edges for each parent relationship
        if (item.parentStories) {
            item.parentStories.forEach(parentId => {
                edges.push({
                    from: parentId,
                    to: item.id,
                    arrows: 'to'
                });
            });
        }
    });

    // Render with vis.js
    const container = document.getElementById('dependency-graph');
    const data = { nodes, edges };
    const options = { /* layout options */ };
    new vis.Network(container, data, options);
}
```

---

## 💾 Data Model Updates

### Schema Changes:

**Task Schema Update:**
```markdown
# TASK-001 | Setup database schema

**Primary Parent**: STORY-001
**Additional Parents**: STORY-002, STORY-005
**Type**: Task
**Status**: IN_PROGRESS
**Priority**: 🔴 CRITICAL

## Parent Relationships
- STORY-001 (Primary) - User authentication
- STORY-002 - User profile management
- STORY-005 - Admin dashboard

## Contribution
**Total Hours**: 8h
**SP per Parent**:
- STORY-001: 3 SP
- STORY-002: 2 SP
- STORY-005: 3 SP
```

**Parser Update:**
```javascript
function parseTaskFile(content) {
    const task = {
        // ... existing fields
        primaryParent: extractMetadata(content, 'Primary Parent'),
        additionalParents: extractListMetadata(content, 'Additional Parents'),
        parentStories: [], // Combined array
    };

    // Combine primary + additional
    task.parentStories = [
        task.primaryParent,
        ...task.additionalParents.split(',').map(s => s.trim())
    ].filter(Boolean);

    return task;
}
```

**Serializer Update:**
```javascript
function serializeTask(task) {
    let md = `# ${task.id} | ${task.title}\n\n`;

    // Primary parent (always required)
    if (task.primaryParent) {
        md += `**Primary Parent**: ${task.primaryParent}\n`;
    }

    // Additional parents (optional)
    if (task.additionalParents && task.additionalParents.length > 0) {
        md += `**Additional Parents**: ${task.additionalParents.join(', ')}\n`;
    }

    // ... rest of serialization

    return md;
}
```

---

## 🔄 Aggregation Logic Updates

### Current Aggregation (Single Parent):
```javascript
async function aggregateToFeature(story) {
    // Find parent feature
    const featureCrumb = breadcrumbs.find(c => c.level === 'feature');

    // Load all stories in feature
    const stories = await loadStoriesInFeature(featureCrumb);

    // Sum up SP
    feature.spTotal = stories.reduce((sum, s) => sum + s.sp, 0);
    feature.spCompleted = stories
        .filter(s => s.status === 'completed')
        .reduce((sum, s) => sum + s.sp, 0);

    await saveFeature(feature);
}
```

### Updated Aggregation (Multiple Parents):
```javascript
async function completeTask(task) {
    task.status = 'completed';
    await saveTask(task);

    // Update ALL parent stories
    const parentStories = [task.primaryParent, ...task.additionalParents];

    for (const storyId of parentStories) {
        const story = await findStoryById(storyId);

        // Recalculate story progress
        await aggregateTasksToStory(story);

        // Trigger parent feature aggregation
        await aggregateToFeature(story);
    }
}

async function aggregateTasksToStory(story) {
    // Load all tasks that reference this story
    const tasks = await findTasksByParentStory(story.id);

    // Calculate completion
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;

    story.tasksCompleted = completedTasks;
    story.tasksTotal = totalTasks;
    story.progress = totalTasks > 0 ? (completedTasks / totalTasks * 100) : 0;

    await saveStory(story);
}
```

---

## 🎯 Implementation Stappenplan

### Phase 1: Data Model (Week 1)
- [ ] Add `primaryParent` field to Task/Story schema
- [ ] Add `additionalParents` array field
- [ ] Update parseTaskFile() to read parent arrays
- [ ] Update serializeTask() to write parent arrays
- [ ] Test: Create task with multiple parents manually

### Phase 2: UI Basics (Week 2)
- [ ] Show parent count in task card: "🔗 3 parents"
- [ ] Add "Parent Stories" section in edit modal
- [ ] Primary parent dropdown
- [ ] Additional parents list with "+" and "×" buttons
- [ ] Test: Edit task and add/remove parents via UI

### Phase 3: Aggregation (Week 3)
- [ ] Update completeTask() to update all parents
- [ ] Update aggregateToFeature() to handle shared stories
- [ ] Add findTasksByParentStory() helper
- [ ] Test: Complete shared task, verify all parents update

### Phase 4: Advanced UI (Week 4)
- [ ] Dependency graph view (vis.js)
- [ ] "Show all parent stories" modal
- [ ] "Show all child tasks across stories" view
- [ ] Filter: "Show only shared tasks"
- [ ] Test: Navigate complex dependency graphs

---

## 📊 Real-World Example

### Scenario: Authentication System

```
EPIC-001: User Management
├── FEATURE-001: Authentication
│   ├── STORY-001: Login flow
│   │   ├── TASK-001: Database schema (SHARED) ←┐
│   │   ├── TASK-002: Login API endpoint          │
│   │   └── TASK-003: Login UI                    │
│   └── STORY-002: Registration                    │
│       ├── TASK-001: Database schema (SHARED) ←──┤ Same task!
│       ├── TASK-004: Registration API            │
│       └── TASK-005: Registration UI             │
└── FEATURE-002: User Profile                      │
    └── STORY-003: Profile management              │
        ├── TASK-001: Database schema (SHARED) ←──┘
        ├── TASK-006: Profile API
        └── TASK-007: Profile UI
```

**TASK-001 metadata:**
```markdown
# TASK-001 | Setup user database schema

**Primary Parent**: STORY-001
**Additional Parents**: STORY-002, STORY-003
**Status**: COMPLETED

## Parent Stories
- STORY-001: Login flow
- STORY-002: Registration
- STORY-003: Profile management

## Description
Creates users table, authentication tables, and profile tables.
This is foundational infrastructure needed by all user-related features.

## Hours Logged
**Total**: 12h
**Distribution**:
- STORY-001: 4h (login tables)
- STORY-002: 4h (registration tables)
- STORY-003: 4h (profile tables)
```

**Effect van completion:**
```
When TASK-001 status → COMPLETED:
1. STORY-001 progress updates (1/3 tasks done = 33%)
2. STORY-002 progress updates (1/3 tasks done = 33%)
3. STORY-003 progress updates (1/3 tasks done = 33%)
4. FEATURE-001 aggregates (2 stories updated)
5. FEATURE-002 aggregates (1 story updated)
6. EPIC-001 aggregates (all features updated)
```

---

## 🤔 Design Decisions

### Vraag 1: Hoe visualiseren in folder structure?

**Decision**: Keep current tree structure, use metadata for relationships
- **Reasoning**: Filesystem is niet gemaakt voor graphs, wel voor trees
- **Alternative**: Reference files (symlinks) maar dat is complexer
- **Tradeoff**: Metadata-based is simpeler maar minder "fysiek zichtbaar"

### Vraag 2: Hoe SP verdelen bij shared tasks?

**Decision**: Full SP to all parents (duplicate counting acceptable)
- **Reasoning**: Als task blocking is voor story, dan is hele impact relevant
- **Alternative**: Split SP (maar dan complexe fractional math)
- **Tradeoff**: SP totals kunnen "hoger" lijken maar dat reflecteert blocked work

### Vraag 3: Primaire parent of geen hiërarchie?

**Decision**: Behoud primary parent concept
- **Reasoning**: Items moeten ergens "leven" in filesystem
- **Alternative**: Flat structure met pure references
- **Tradeoff**: Meer complexity maar behoudt huidige file structure

---

## 💭 Aanbeveling

**Start met Optie 1 (Reference-Based Model):**

1. Simpelste implementatie
2. Geen extra bestanden
3. Behoud huidige folder structure
4. Metadata-driven = flexible
5. Kan later uitbreiden naar visual graph

**Implementatie volgorde:**
1. Week 1: Schema updates (metadata fields)
2. Week 2: Edit modal (add/remove parents)
3. Week 3: Aggregation updates (all parents)
4. Week 4: UI polish (graph view, indicators)

**Minimum Viable Implementation (1 dag werk):**
- Add `parentStories` array to Task
- Show count in card: "🔗 3 stories"
- Edit modal: add parent selector
- Update aggregation to loop through parents

---

**Datum**: 2025-11-12
**Versie**: 1.0
**Status**: Design Document - Not Yet Implemented
