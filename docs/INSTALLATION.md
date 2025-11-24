# Installation Guide

> **[Back to README](../README.md)**

This guide covers all installation options for Markdown Task Manager.

---

## Prerequisites

- **Compatible browser**: Chrome 86+, Edge 86+ or Opera 72+
- File System Access API is not available on Firefox or Safari

---

## Quick Start (3 steps)

1. **Download** `task-manager.html` from this repository
2. **Open it** in your browser (double-click)
3. **Select** a folder to store your tasks

That's all!

---

## First Use

On first launch:
1. The application requests access to a folder
2. If the folder is empty, it automatically creates:
   - `kanban.md` - Your active tasks
   - `archive.md` - Your archived tasks
3. You can give a name to the project
4. The project is remembered for next sessions

---

## Project Installation Options

### Option 1: Root installation (recommended)

Simply copy 2 files to your project root:

```bash
my-project/
├── kanban.md          # <- Create this file (see template below)
├── archive.md         # <- Create this file (see template below)
├── src/
├── package.json
└── README.md
```

**Minimal kanban.md template:**
```markdown
# Kanban Board

## Configuration

**Columns**: To Do | In Progress | Done
**Categories**: Frontend, Backend, Design
**Users**: @alice, @bob
**Tags**: #bug, #feature, #docs

## To Do

## In Progress

## Done
```

**Minimal archive.md template:**
```markdown
# Task Archive

> Archived tasks from the project

## Archives
```

Then:
1. Open `task-manager.html` in your browser
2. Select the `my-project/` folder
3. Start creating tasks!

### Option 2: Subdirectory installation

If you prefer to isolate task files:

```bash
my-project/
├── .tasks/            # <- or docs/tasks/, .kanban/, etc.
│   ├── kanban.md
│   └── archive.md
├── src/
└── package.json
```

Then, select the `.tasks/` folder when opening the application.

### Option 3: Add to .gitignore (optional)

If you don't want to version your tasks:

```bash
# .gitignore
kanban.md
archive.md
# or
.tasks/
```

**Note:** It is generally recommended to **version** task files to keep history and sync with the team.

---

## HTML File Management

You have 2 options to manage `task-manager.html`:

### Option A: One copy per project

```bash
project-1/
├── task-manager.html  # <- Local copy
├── kanban.md
└── archive.md

project-2/
├── task-manager.html  # <- Local copy
├── kanban.md
└── archive.md
```

**Advantages:**
- Complete autonomy for each project
- Works even if central file is modified
- Can be versioned with the project

**Disadvantages:**
- HTML file duplication
- Manual update in each project

### Option B: Single centralized file (recommended)

```bash
~/tools/
└── task-manager.html  # <- Single copy

~/projects/
├── project-1/
│   ├── kanban.md
│   └── archive.md
├── project-2/
│   ├── kanban.md
│   └── archive.md
└── project-3/
    ├── kanban.md
    └── archive.md
```

**Advantages:**
- Single file to maintain
- Automatic updates for all projects
- Disk space savings

**Disadvantages:**
- Dependency on external file

**How to use it:**
1. Keep `task-manager.html` in an accessible folder (e.g., `~/tools/`)
2. Create a shortcut/bookmark in your browser
3. Open it and select the desired project folder
4. The application remembers the last 10 projects

**Tip:** Create an alias to open it quickly:

```bash
# ~/.bashrc or ~/.zshrc
alias tasks='open ~/tools/task-manager.html'  # macOS
alias tasks='xdg-open ~/tools/task-manager.html'  # Linux
alias tasks='start ~/tools/task-manager.html'  # Windows
```

---

## Advanced Installation

### With Git

```bash
# Clone repository
git clone https://github.com/your-username/markdown-task-manager.git
cd markdown-task-manager

# Open application
open task-manager.html  # macOS
xdg-open task-manager.html  # Linux
start task-manager.html  # Windows

# Or host locally (optional)
python -m http.server 8000
# Then open http://localhost:8000/task-manager.html
```

### Installation on a new project

```bash
# Create a new project with task system
mkdir my-project
cd my-project
git init

# Copy necessary files
cp /path/to/kanban.md .
cp /path/to/archive.md .
cp /path/to/AI_WORKFLOW.md .        # Optional (for AI)
cp /path/to/CLAUDE.md.exemple CLAUDE.md   # Optional (for Claude)

# First commit
git add .
git commit -m "chore: Initialize task management system"

# Open application
open /path/to/task-manager.html
# Select my-project/ folder
```

### Migration from existing system

**From Trello/Jira/Linear:**
1. Export your tasks to CSV
2. Use a script to convert to Markdown format
3. Import into `kanban.md`

**From GitHub Issues:**
```bash
# Use GitHub CLI
gh issue list --state all --json number,title,body,labels
# Convert to Markdown Task Manager format
```

**From Notion/Obsidian:**
1. Export to Markdown
2. Adjust format to match template
3. Import into application

---

**[Back to README](../README.md)** | **[Features](./FEATURES.md)** | **[AI Integration](./AI_INTEGRATION.md)**
