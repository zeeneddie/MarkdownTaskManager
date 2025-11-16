# Kanban ↔ Project Board Integration Proposal

## 🎯 Doel

Creëer één geïntegreerd systeem waar:
1. **Project Board** = Long-term planning (Epic → Story)
2. **Sprint Board** = Active sprint (Stories → Tasks in uitvoering)
3. **Kanban Board** = Daily work (Individuele taken vandaag/deze week)

## 📊 Voorgestelde Structuur

### Levels & Views:

```
STRATEGIC LEVEL (Months/Quarters)
├── Epics (grote initiatieven)
│   └── Features (capabilities)
│       └── Stories (user stories)
│           └── Tasks (implementatie stappen)
                  ↓
TACTICAL LEVEL (2-week sprints)
├── Sprint Planning View
│   ├── Sprint Backlog (selected stories)
│   ├── Sprint Board (story status)
│   └── Sprint Tasks (tasks voor deze sprint)
                  ↓
OPERATIONAL LEVEL (Daily)
└── Kanban Board (active work today/this week)
    ├── TODO (tasks vandaag)
    ├── IN PROGRESS (bezig nu)
    └── DONE (afgerond vandaag)
```

## 🔗 Relaties Die Moeten Bestaan

### 1. **Story → Sprint** ⭐⭐⭐ (Hoogste prioriteit)

**In Story metadata:**
```markdown
# STORY-001 | User Authentication

**Sprint**: Sprint 3
**Sprint Status**: IN_SPRINT
**Sprint Start**: 2025-11-15
**Sprint End**: 2025-11-29
```

**Views:**
- Sprint Planning: Drag stories naar sprint
- Sprint Board: Kanban per sprint (Stories als kolommen)
- Sprint Backlog: Lijst van stories in sprint

### 2. **Task → Sprint** ⭐⭐⭐

**In Task metadata:**
```markdown
# TASK-001 | Setup database

**Story**: STORY-001
**Sprint**: Sprint 3
**In Kanban**: Yes
**Kanban Status**: in-progress
**Assigned**: @eddie
```

**Betekenis:**
- Tasks kunnen in active sprint zitten
- Tasks in sprint kunnen op kanban board
- Sync status tussen project en kanban

### 3. **Sprint Planning View** ⭐⭐⭐

**Nieuwe view in project-manager.html:**

```
┌─────────────────────────────────────────────────┐
│  Sprint 3: Authentication & Authorization       │
│  📅 Nov 15 - Nov 29 (2 weeks)                   │
│  📊 25 SP / 34 SP total (74%)                   │
└─────────────────────────────────────────────────┘

PLANNED STORIES (10 SP):
├── STORY-001: User login (5 SP)
│   └── Tasks: 3 tasks, 2 completed
└── STORY-002: OAuth integration (5 SP)
    └── Tasks: 4 tasks, 0 completed

IN PROGRESS (8 SP):
└── STORY-003: Password reset (8 SP)
    └── Tasks: 2/5 completed

COMPLETED (7 SP):
└── STORY-004: User registration (7 SP)
    └── Tasks: 5/5 completed

SPRINT ACTIONS:
[+ Add Story] [Start Sprint] [Complete Sprint] [Burndown Chart]
```

### 4. **Kanban ↔ Project Sync** ⭐⭐

**Optie A: Kanban als "Active Work" View**
- Kanban toont alleen tasks van **current sprint**
- Tasks worden automatisch naar kanban gepushed bij sprint start
- Status sync: kanban → project bidirectioneel

**Optie B: Kanban als Aparte Layer**
- Kanban voor ad-hoc werk (bugs, support, etc.)
- Project tasks kunnen "promoted" worden naar kanban
- Link via `parent: STORY-001` in kanban task

**Aanbeveling**: Optie A (Kanban = Active Sprint Tasks)

### 5. **Task Dependencies** ⭐⭐

**In Task metadata:**
```markdown
# TASK-003 | Migrate user data

**Depends On**: TASK-001, TASK-002
**Blocks**: TASK-005
**Status**: BLOCKED (waiting on TASK-001)
```

**Visualisatie:**
- Dependency graph (wie wacht op wie)
- Critical path berekening
- Blocked tasks warning

### 6. **Team Member Workload** ⭐

**Cross-cutting view:**
```
@eddie (Current Sprint Load: 13 SP)
├── STORY-001: User login (5 SP) - IN_PROGRESS
├── TASK-005: Write tests (3h) - TODO
└── TASK-008: Code review (2h) - IN_PROGRESS

@alice (Current Sprint Load: 8 SP)
├── STORY-002: OAuth (8 SP) - PLANNED
└── TASK-006: Design mockups (4h) - DONE
```

### 7. **Epic → Sprint Contribution** ⭐

**Epic view shows sprint breakdown:**
```
EPIC-001: User Management (100 SP)

Sprint 1 (Nov 1-14):   12 SP completed ✅
Sprint 2 (Nov 15-28):   8 SP completed ✅
Sprint 3 (Nov 29-Dec12): 15 SP planned  🚀
Sprint 4 (Dec 13-26):   20 SP planned  📋
Future sprints:         45 SP remaining ⏳
```

## 🎨 UI/UX Voorstellen

### Navigation Structuur:

```
Top Navigation:
┌────────────────────────────────────────────────┐
│ [📊 Dashboard] [📁 Projects] [🏃 Sprints] [📋 Kanban] │
└────────────────────────────────────────────────┘

Dashboard:
- Active sprint overview
- My tasks today
- Team velocity
- Blockers / Impediments

Projects:
- Current: project-manager.html view
- Epic → Feature → Story → Task

Sprints:
- Sprint planning
- Sprint board (story kanban)
- Burndown chart
- Retrospective notes

Kanban:
- Current: task-manager.html
- But filtered to active sprint tasks
- Daily standup view
```

### Nieuwe Views Nodig:

#### 1. **Sprint Planning View**
```javascript
// Nieuwe file: sprint-planner.html
- Drag stories van backlog naar sprint
- Capacity planning (SP vs team capacity)
- Sprint goal definitie
- Auto-calculate sprint dates
```

#### 2. **Sprint Board View**
```javascript
// In project-manager.html
- Filter op current sprint
- Group by story
- Task status per story
- Real-time burndown
```

#### 3. **Integrated Kanban**
```javascript
// Update task-manager.html
- Show parent story for each task
- Link to story detail
- Sprint indicator
- Auto-filter to current sprint
```

#### 4. **Dashboard View**
```javascript
// Nieuwe file: dashboard.html
- Active sprint widget
- My tasks widget
- Team velocity chart
- Recent activity feed
```

## 🔧 Implementatie Plan

### Phase 1: Sprint Support (Week 1)
- [ ] Add Sprint metadata to Story
- [ ] Sprint filter in project-manager
- [ ] Sprint view (list of stories in sprint)
- [ ] Sprint planning drag-and-drop

### Phase 2: Kanban Integration (Week 2)
- [ ] Add parent story link to tasks
- [ ] Kanban filter: "Show only current sprint"
- [ ] Bidirectional sync: kanban ↔ project
- [ ] Auto-push tasks to kanban on sprint start

### Phase 3: Advanced Views (Week 3)
- [ ] Sprint board (story kanban)
- [ ] Burndown chart
- [ ] Team workload view
- [ ] Dependency graph

### Phase 4: Dashboard (Week 4)
- [ ] Unified dashboard
- [ ] My tasks view
- [ ] Team velocity tracking
- [ ] Notifications / blockers

## 📐 Data Model Changes

### Story Schema Update:
```markdown
# STORY-001 | User Authentication

**Parent**: `../../feature.md` (FEATURE-001)
**Type**: Story
**Priority**: 🟠 HIGH
**Status**: IN_PROGRESS

# NEW FIELDS:
**Sprint**: Sprint-2025-11-15  # Sprint identifier
**Sprint Status**: IN_SPRINT   # NOT_PLANNED, PLANNED, IN_SPRINT, COMPLETED
**Sprint Start**: 2025-11-15
**Sprint End**: 2025-11-29
**Sprint Goal**: Implement user authentication flow

## Story Points
**SP**: 5

## Sprint Progress
**Tasks Completed**: 2/5
**Hours Logged**: 8/12
**Burndown**: On track ✅
```

### Task Schema Update:
```markdown
# TASK-001 | Setup database schema

**Parent**: `../story.md` (STORY-001)
**Type**: Task
**Status**: IN_PROGRESS

# NEW FIELDS:
**Sprint**: Sprint-2025-11-15   # Inherited from story
**Kanban Sync**: Yes            # Is this on kanban board?
**Kanban Status**: in-progress  # Mirror of project status
**Sync Last**: 2025-11-12 14:30 # Last sync timestamp

# NEW: Dependencies
**Depends On**: TASK-002        # Blocked until this done
**Blocks**: TASK-005           # Others waiting on this
**Dependency Status**: READY    # READY, BLOCKED, WAITING
```

### NEW: Sprint Schema
```markdown
# Sprint-2025-11-15

**Project**: HCI EPD Modernisation
**Sprint Number**: 3
**Start Date**: 2025-11-15
**End Date**: 2025-11-29
**Duration**: 14 days (2 weeks)
**Status**: ACTIVE

## Sprint Goal
Implement complete user authentication and authorization system.

## Capacity
**Team Size**: 3 developers
**Available Hours**: 120h (3 devs × 40h)
**Planned SP**: 34
**Committed SP**: 25

## Stories in Sprint
- STORY-001: User login (5 SP) - IN_PROGRESS
- STORY-002: OAuth integration (5 SP) - PLANNED
- STORY-003: Password reset (8 SP) - IN_PROGRESS
- STORY-004: User registration (7 SP) - COMPLETED

## Metrics
**Velocity (avg last 3 sprints)**: 28 SP
**Burndown**: See burndown.csv
**Completion Rate**: 74% (25/34 SP)

## Retrospective
(Added at end of sprint)
```

## 🗂️ Folder Structure Update

```
example-project/
├── project.md
├── sprints/                           # NEW!
│   ├── SPRINT-2025-11-01/
│   │   ├── sprint.md                  # Sprint metadata
│   │   ├── burndown.csv               # Daily burndown data
│   │   ├── retrospective.md           # Retro notes
│   │   └── stories/                   # Symlinks? or references?
│   ├── SPRINT-2025-11-15/             # Active sprint
│   │   ├── sprint.md
│   │   └── burndown.csv
│   └── SPRINT-2025-11-29/             # Next sprint
│       └── sprint.md (PLANNED)
├── epics/
│   └── EPIC-001-assessment/
│       ├── epic.md
│       └── features/
│           └── FEATURE-001-codebase-analysis/
│               ├── feature.md
│               └── stories/
│                   └── STORY-001-metrics/
│                       ├── story.md      # NOW has Sprint field
│                       └── tasks/
│                           └── TASK-001.md  # NOW has Sprint + Kanban fields
└── kanban.md                          # NOW synced with sprint tasks
```

## 🎯 Key Questions to Answer

### 1. **Waar leven Sprint gegevens?**

**Optie A: In Story files**
```markdown
# STORY-001
**Sprint**: Sprint-2025-11-15
```
- ✅ Simple, geen extra files
- ❌ Geen centrale sprint view

**Optie B: Separate Sprint folders** (AANBEVOLEN)
```
sprints/
├── SPRINT-2025-11-15/
│   ├── sprint.md (metadata)
│   └── stories.txt (list of STORY-001, STORY-002)
```
- ✅ Centrale sprint management
- ✅ Sprint history behouden
- ✅ Burndown charts per sprint
- ❌ Extra complexity

### 2. **Hoe sync Kanban ↔ Project?**

**Optie A: Kanban is View** (AANBEVOLEN)
- kanban.md wordt dynamisch gegenereerd
- Source of truth = project tasks
- Kanban is filtered view of "active sprint tasks"

**Optie B: Bidirectional Sync**
- kanban.md en task files both exist
- Sync mechanism updates both
- Conflict resolution needed

**Optie C: Kanban References**
```markdown
# In kanban.md
## TODO
- [ ] Setup database (ref: TASK-001) @eddie
- [ ] Write tests (ref: TASK-005) @alice
```
- ✅ Lightweight
- ✅ Easy to implement
- ❌ Manual maintenance

### 3. **Story Points op Task level?**

**Huidige**: Tasks hebben Hours, Stories hebben SP

**Alternatief**: Tasks ook SP?
- Break story SP down to tasks
- Sum task SP = story SP
- Better granularity

**Aanbeveling**: Behoud huidige (Story = SP, Task = Hours)

## 🚀 Quick Wins (Kan NU)

### 1. Add Sprint Field to Stories
```javascript
// In serializeStory()
if (story.sprint) md += `**Sprint**: ${story.sprint}\n`;
```

### 2. Sprint Filter in UI
```javascript
// In project-manager.html
<select id="sprintFilter">
  <option value="">All Sprints</option>
  <option value="Sprint-2025-11-15">Sprint 3 (Active)</option>
  <option value="Sprint-2025-11-01">Sprint 2</option>
</select>
```

### 3. Parent Story in Kanban
```javascript
// In task-manager.html
// Show story context for task
<div class="task-card">
  <div class="task-title">Setup database</div>
  <div class="task-parent">📖 STORY-001: User Auth</div>
</div>
```

## 💭 Mijn Aanbeveling

**Start met Sprint Support:**

1. **Week 1**: Add Sprint metadata to stories
   - Sprint field in story.md
   - Sprint filter in project manager
   - "Current Sprint" badge

2. **Week 2**: Sprint Planning View
   - List stories by sprint
   - Drag-drop to assign sprint
   - Sprint capacity calculation

3. **Week 3**: Integrate Kanban
   - Link kanban tasks to stories
   - Show parent story
   - Filter kanban to active sprint

4. **Week 4**: Sprint Board & Metrics
   - Sprint burndown
   - Team velocity
   - Sprint retrospective notes

**Focus op praktisch gebruik**, niet perfecte architectuur!

