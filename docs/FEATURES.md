# Application Features

> **[Back to README](../README.md)**

Complete guide to all Markdown Task Manager features.

---

## 1. Interactive Kanban View

![Kanban Board](images/kanban-board.jpg)
*Interactive Kanban board with drag & drop, customizable columns, and task counters*

- **Customizable columns**: Create and organize your own columns
  - Default: To Do, In Progress, Review, Done
  - Modifiable via "Columns" button
- **Drag & Drop**: Move tasks between columns by dragging
- **Adaptive layout**: Centered columns using full screen width
- **Counters**: Number of tasks displayed in each column

---

## 2. Complete Task Management

![Task Creation Modal](images/task-modal.jpg)
*Complete task creation and editing modal with all metadata fields and subtasks*

**Creation:**
- Complete form with all fields
- Auto-generated ID (TASK-XXX)
- Required field validation

**Rich metadata:**
- **Title**: Unique identifier and short description
- **Priority**: Critical, High, Medium, Low (color coded)
- **Category**: Customizable (Frontend, Backend, etc.)
- **Assignment**: Multiple users possible (@user1, @user2)
- **Tags**: Multiple tags (#bug, #feature, etc.)
- **Dates**: Creation, start, due, end
- **Description**: Free text with Markdown support

**Subtasks:**
- Create, edit, delete subtasks
- Check/uncheck in real time
- Visual progress bar
- Counter (e.g., "3/5 subtasks completed")

**Editing:**
- Detailed editing modal for each task
- Modification of all fields
- Instant preview
- Auto-save

---

## 3. Advanced Filters

![Advanced Filters](images/filters.jpg)
*Advanced filtering system with priority, tags, categories, and users filters*

**4 types of cumulative filters:**

1. **Priority** (color-coded badges)
   - Filter by task priority level
   - Options: Critical, High, Medium, Low
   - Quickly identify urgent tasks

2. **Tags** (blue bubbles)
   - Filter by one or more tags
   - Example: #bug, #urgent, #backend

3. **Categories** (purple bubbles)
   - Filter by task category
   - Example: Frontend, Backend, Design

4. **Users** (green bubbles)
   - Filter by assignment
   - Example: @alice, @bob

**How it works:**
- Select a filter via dropdowns
- Click on a badge in a task to filter instantly
- Combine multiple filters (AND logic)
- Remove a filter individually (x on bubble)
- Clear all filters at once

**Smart autocomplete:**
- Filters remember history
- Even archived values remain available
- Contextual suggestions during input

---

## 4. Archive System

![Archive View](images/archives.jpg)
*Archive view showing completed tasks with search and restoration capabilities*

**Archiving:**
- Move completed tasks to `archive.md`
- Manual archiving (button in task)
- Organization by sections (e.g., by month, by sprint)

**Consultation:**
- Dedicated archive view ("Archives" button)
- Search in archives
- Detailed display of each archived task

**Restoration:**
- Restore a task to kanban
- Task returns to its original column
- Metadata preserved

**Persistent history:**
- Tags/categories/users from archived tasks remain in autocomplete
- Allows maintaining consistency between projects

---

## 5. Global Search

**Powerful search functionality:**
- Search across all active tasks
- Search through archived tasks
- Real-time filtering as you type
- Search in task titles, descriptions, and metadata

**Search features:**
- Find tasks by ID (e.g., "TASK-042")
- Search by keywords in title or description
- Filter results by column
- View archived tasks matching your search

**Accessibility:**
- Quick access via search button in header
- Dedicated search modal
- Clear results presentation

---

## 6. Interface Translation

**Multi-language support:**
- English and French languages available
- Language selector in application settings
- Complete interface translation
- Seamless language switching

**Translated elements:**
- All UI buttons and labels
- Form fields and placeholders
- Column names and status messages
- Help text and instructions
- Error messages and notifications

**Note:** The markdown files (kanban.md, archive.md) content remains in your chosen language.

---

## 7. Multi-Project

![Multi-Project Selector](images/multi-project.jpg)
*Quick project switcher showing recent projects with custom names*

**Project management:**
- Memorization of last 10 projects used
- Quick selector in header (dropdown)
- Custom names for each project
- Memorized file paths

**Navigation:**
- Instant project change
- Auto-restore last project on launch
- Button to rename current project

**Storage:**
- Uses IndexedDB to store directory handles
- No need to re-select folder each time
- Persistent browser permissions

---

## 8. Auto-Save

- **Immediate save**: Each modification is written instantly
- **No "Save" button**: Everything is automatic
- **Synchronization**: Markdown files always stay up to date
- **External editing compatible**: You can edit files manually

---

## 9. Other Features

- **Export**: Your Markdown files are already exported!
- **Theme**: Modern and clean interface
- **Responsive**: Works on different screen sizes
- **Keyboard shortcuts**: Quick navigation (coming soon)
- **Dark mode**: Light/dark toggle (coming soon)

---

## File Structure

### Main files

```
your-project/
├── kanban.md          # Active tasks (required)
├── archive.md         # Archived tasks (required)
├── AI_WORKFLOW.md     # Guidelines for AI (optional)
└── [AI file].md       # Specific AI configuration (optional)
```

### Content of kanban.md

```markdown
# Kanban Board

<!-- Config: Last Task ID: 42 -->

## Configuration

**Columns**: To Do (todo) | In Progress (in-progress) | Done (done)
**Categories**: Frontend, Backend, Design
**Users**: @alice (Alice Martin), @bob (Bob Smith)
**Tags**: #bug, #feature, #docs, #refactor

---

## To Do

### TASK-001 | My first task
**Priority**: High | **Category**: Frontend | **Assigned**: @alice
**Created**: 2025-01-20 | **Due**: 2025-02-01
**Tags**: #feature #ui

Task description...

**Subtasks**:
- [ ] First subtask
- [x] Completed subtask
- [ ] Last subtask

## In Progress

### TASK-002 | Other task
...

## Done

### TASK-003 | Completed task
...
```

### Content of archive.md

```markdown
# Task Archive

> Archived tasks from project My Project

## January 2025

### TASK-042 | Implement notification system
**Priority**: High | **Category**: Backend | **Assigned**: @alice
**Created**: 2025-01-15 | **Started**: 2025-01-18 | **Finished**: 2025-01-22
**Tags**: #feature #notifications

Real-time notification system with WebSockets.

**Subtasks**:
- [x] Setup WebSocket server
- [x] Create REST API
- [x] Implement email sending
- [x] Notifications UI
- [x] End-to-end tests

**Notes**:

**Result**:
Functional notification system with WebSocket, REST API and emails.

**Modified files**:
- src/websocket/server.js (lines 1-150)
- src/api/notifications.js (lines 20-85)
- src/ui/NotificationPanel.jsx (lines 1-200)

**Technical decisions**:
- Socket.io for WebSockets (simpler than native ws)
- SendGrid for emails (100/day free quota)
- 30-day history in MongoDB

**Tests performed**:
- 100 simultaneous connections OK
- Automatic reconnection after disconnect
- Emails sent in < 2s

---

## December 2024

### TASK-001 | Old archived task
...
```

---

## User Interface

### Header

```
+------------------------------------------------------------------+
| Task Manager  [Project v] [Edit] [Open] [New] [Archives] [Cols]  |
+------------------------------------------------------------------+
```

Buttons:
- **[Project v]**: Recent project selector
- **[Edit]**: Rename current project
- **[Open folder]**: Select/change folder
- **[New task]**: Create a task
- **[Archives]**: View archived tasks
- **[Columns]**: Manage Kanban columns

### Filter bar

```
+------------------------------------------------------------------+
|  Tags: [Select v] [+]   Category: [Select v] [+]   User: [v]     |
|                                                                    |
|  #bug x    #urgent x    Frontend x    @alice x                    |
+------------------------------------------------------------------+
```

### Task card (details)

```
+----------------------------------------------+
| TASK-042 | Implement notification system     |
+----------------------------------------------+
| Priority: High                               |
| Category: Backend                            |
| Assigned: @alice, @bob                       |
| Created: 2025-01-15                          |
| Due: 2025-02-01                              |
| Tags: #feature #notifications                |
+----------------------------------------------+
| Detailed task description...                 |
|                                              |
| Subtasks (3/5):                              |
| [x] Setup WebSocket server                   |
| [x] Create REST API                          |
| [x] Implement email sending                  |
| [ ] Notifications UI                         |
| [ ] End-to-end tests                         |
+----------------------------------------------+
| [Edit] [Archive] [Delete] [Close]            |
+----------------------------------------------+
```

---

**[Back to README](../README.md)** | **[Installation](./INSTALLATION.md)** | **[Configuration](./CONFIGURATION.md)**
