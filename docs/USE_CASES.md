# Use Cases

> **[Back to README](../README.md)**

Real-world scenarios for using Multi-Stack AI Agent Platform effectively.

---

## 1. Software Development

### Backlog management
- Create tasks from GitHub issues
- Plan sprints
- Track team velocity

### Bug tracking
- Tag `#bug` + critical priority
- Assignment to developers
- Resolution documentation

### Code reviews
- Dedicated column "Review"
- Review checklist in subtasks
- Archiving with technical decisions

---

## 2. Project Management

### Product roadmap
- Create tasks for each feature
- Deadlines and milestones
- Progress tracking

### Team collaboration
- Multi-user assignment
- Filter by person
- Real-time visibility via Git

### Retrospectives
- Search in archives
- Statistics on completed tasks
- Velocity analysis

---

## 3. Personal Use

### Advanced ToDo lists
- Organize tasks by project
- Subtasks to break down
- Archives for history

### Personal projects
- Track side-projects
- Notes and learnings
- Goals with deadlines

### Journaling
- Task = journal entry
- Tags to categorize
- Archives = complete journal

---

## 4. Distributed Teams

### Git synchronization

```bash
git pull origin main          # Get updates
# Work in the application
git add kanban.md archive.md
git commit -m "Update tasks"
git push origin main          # Share with team
```

### Conflict resolution

```bash
# In case of conflict on kanban.md
git checkout --theirs kanban.md  # Take remote version
# or
git checkout --ours kanban.md    # Keep local version
# or resolve manually (simple Markdown format)
```

### Branch workflow

```bash
# Create a branch per feature
git checkout -b feature/TASK-042-notifications

# Reference task in commits
git commit -m "feat: Add WebSocket server (TASK-042 - 1/5)"
git commit -m "feat: Add notification API (TASK-042 - 2/5)"

# Merge and archive
git checkout main
git merge feature/TASK-042-notifications
# Move TASK-042 to "Done" then archive
```

---

## Getting Started Scenarios

### Scenario 1: Solo developer on personal project

```bash
# 1. Download task-manager.html to ~/tools/
cd ~/tools
# [Download task-manager.html]

# 2. Create a new project
cd ~/projects
mkdir my-app
cd my-app
git init

# 3. Create task files
cat > kanban.md << 'EOF'
# Kanban Board

## Configuration

**Columns**: To Do | In Progress | Done
**Categories**: Frontend, Backend, Database
**Users**: @me
**Tags**: #feature, #bug, #refactor

## To Do
## In Progress
## Done

<!-- Config: Last Task ID: 000 -->
EOF

cat > archive.md << 'EOF'
# Task Archive
## Archives
EOF

# 4. Open application
open ~/tools/task-manager.html

# 5. Select my-app/ folder

# 6. Create your first task!
```

### Scenario 2: Team migrating from Trello

```bash
# 1. Install for team
git clone https://github.com/team/project.git
cd project

# 2. Add task system
cp ~/downloads/kanban.md .
cp ~/downloads/archive.md .
git add kanban.md archive.md
git commit -m "chore: Add task management system"
git push

# 3. Each team member:
# - Downloads task-manager.html
# - Clone/pull project
# - Opens task-manager.html
# - Selects project/ folder

# 4. Daily workflow:
git pull                    # Get updates
# [Work in app]
git add kanban.md
git commit -m "Update tasks"
git push                    # Share with team
```

### Scenario 3: Integration with Claude/ChatGPT

```bash
# 1. Complete installation with AI
cd my-project
cp ~/downloads/kanban.md .
cp ~/downloads/archive.md .
cp ~/downloads/AI_WORKFLOW.md .
cp ~/downloads/CLAUDE.md.exemple CLAUDE.md

# 2. First session with Claude
# Say: "Read CLAUDE.md and create a task to implement an auth system"

# 3. Claude will automatically:
# - Create TASK-001 in kanban.md
# - Break down into subtasks
# - Update as it progresses
# - Document result

# 4. You can visualize in app
open ~/tools/task-manager.html
# [Select my-project/]
# See TASK-001 with all subtasks checked!
```

---

**[Back to README](../README.md)** | **[Configuration](./CONFIGURATION.md)** | **[Compatibility](./COMPATIBILITY.md)**
