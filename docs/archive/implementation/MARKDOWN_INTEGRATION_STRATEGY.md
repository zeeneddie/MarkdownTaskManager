# Markdown-First Integration Strategy

**Date:** 2025-11-12
**Version:** 1.0

## Executive Summary

Instead of building a new system from scratch, we integrate the **existing project.md** hierarchical structure with the new FastAPI backend and agentic capabilities. This provides:

1. ✅ **Human-friendly editing** - project.md remains the primary interface
2. ✅ **Version control** - Git tracks all changes to markdown files
3. ✅ **No lock-in** - Markdown files are portable and tool-agnostic
4. ✅ **Agent power** - Backend adds automation, estimation, and intelligence
5. ✅ **Analytics** - Database enables search, reporting, and metrics

---

## 1. Current State Analysis

### Existing Assets

**Frontend:**
- `project-manager.html` - Hierarchical project management UI
- `task-manager.html` - Kanban board UI
- Both use File System Access API to read/write markdown files directly

**Markdown Files:**
- `project.md` - Epic → Feature → Story → Task hierarchy
- `kanban.md` - Simple kanban board
- `archive.md` - Completed tasks
- `project-archive.md` - Archived projects

**Backend (Just Built):**
- FastAPI with 45 REST endpoints
- PostgreSQL database with hierarchical schema
- Alembic migrations
- JWT authentication

### Current Workflow

```
User → project-manager.html → File System API → project.md (write)
                              ↑
                              └── (read) project.md
```

**Limitations:**
- No agent automation
- No estimation engine
- No real-time collaboration
- No analytics/reporting
- Single-user (file locking issues)

---

## 2. Proposed Architecture: Markdown-First with Backend Sync

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: MARKDOWN FILES (Source of Truth)                  │
│  - project.md (Epic/Feature/Story/Task)                     │
│  - kanban.md (Simple tasks)                                 │
│  - Git version control                                      │
└─────────────────────────────────────────────────────────────┘
                            ↕ (Bidirectional Sync)
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: SYNC ENGINE                                       │
│  - Markdown Parser (read .md → database)                    │
│  - Markdown Generator (write database → .md)                │
│  - File watcher (auto-sync on changes)                      │
│  - Conflict resolution                                      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: DATABASE (PostgreSQL)                             │
│  - Structured data for querying                             │
│  - Analytics and reporting                                  │
│  - Agent work queue                                         │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: BACKEND API (FastAPI)                             │
│  - REST endpoints (45 endpoints)                            │
│  - WebSocket for real-time updates                          │
│  - Agent coordination                                       │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: AGENT LAYER (KaibanJS)                            │
│  - 8 specialized agents                                     │
│  - Read/write to database + markdown                        │
│  - Estimation, quality gates, testing                       │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: FRONTEND (Multiple UIs)                           │
│  - project-manager.html (existing, enhanced)                │
│  - WebSocket client for real-time updates                   │
│  - Agent activity dashboard                                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Examples

**User Creates Epic via UI:**
```
User → project-manager.html → POST /api/epics
                               ↓
                            FastAPI validates
                               ↓
                            PostgreSQL insert
                               ↓
                            Sync Engine writes to project.md
                               ↓
                            Git detects change (optional auto-commit)
                               ↓
                            WebSocket broadcast to all clients
```

**Agent Estimates Story Points:**
```
Agent (Estimation Engine) → Read from PostgreSQL
                            ↓
                         Calculate SP (Fibonacci)
                            ↓
                         Update PostgreSQL (sp field)
                            ↓
                         Sync Engine updates project.md
                            ↓
                         WebSocket broadcast
```

**User Edits project.md Directly:**
```
User → vim project.md (edit STORY-001 SP from 5 to 8)
       ↓
    Save file
       ↓
    File Watcher detects change
       ↓
    Sync Engine parses project.md
       ↓
    Update PostgreSQL (STORY-001.sp = 8)
       ↓
    WebSocket broadcast
       ↓
    project-manager.html auto-refreshes
```

---

## 3. Sync Engine Design

### 3.1 Markdown Parser

**Purpose:** Parse project.md into structured data for database

**Technology:** Python with regex + markdown parser (markdown-it-py)

**Parsing Logic:**

```python
import re
from typing import List, Dict
from datetime import datetime

class ProjectMarkdownParser:
    """Parse project.md hierarchical structure"""

    def parse_file(self, file_path: str) -> Dict:
        """Parse entire project.md file"""
        with open(file_path, 'r') as f:
            content = f.read()

        # Extract configuration
        config = self._parse_config(content)

        # Extract all epics
        epics = self._parse_epics(content)

        return {
            'config': config,
            'epics': epics,
            'parsed_at': datetime.utcnow()
        }

    def _parse_config(self, content: str) -> Dict:
        """Extract config from markdown comments"""
        # <!-- Config: Last Epic ID: 0, Last Feature ID: 0, ... -->
        config_pattern = r'<!-- Config: (.*?) -->'
        match = re.search(config_pattern, content)

        if not match:
            return {}

        config_str = match.group(1)
        config = {}

        for item in config_str.split(','):
            if ':' in item:
                key, value = item.split(':', 1)
                config[key.strip()] = value.strip()

        return config

    def _parse_epics(self, content: str) -> List[Dict]:
        """Extract all epics with nested features/stories/tasks"""
        epics = []

        # Match: ### EPIC-001 | Title
        epic_pattern = r'### (EPIC-\d+) \| (.+?)$'

        # Split content by sections (PLANNED, IN PROGRESS, TESTING, COMPLETED)
        sections = re.split(r'## 📋 PLANNED|## 🚀 IN PROGRESS|## 🧪 TESTING|## ✅ COMPLETED', content)

        for section in sections:
            for match in re.finditer(epic_pattern, section, re.MULTILINE):
                epic_id = match.group(1)
                epic_title = match.group(2)

                # Extract epic metadata (Type, Priority, Status, etc.)
                epic_data = self._extract_epic_metadata(section, epic_id)
                epic_data['id'] = epic_id
                epic_data['title'] = epic_title
                epic_data['type'] = 'epic'

                # Extract nested features
                epic_data['features'] = self._parse_features(section, epic_id)

                epics.append(epic_data)

        return epics

    def _extract_epic_metadata(self, section: str, epic_id: str) -> Dict:
        """Extract metadata for an epic"""
        metadata = {}

        # Extract after EPIC-XXX line until next epic or feature
        epic_section = self._extract_section_after_id(section, epic_id)

        # Parse metadata lines
        # **Type**: 🔧 TECHNICAL | **Priority**: 🟠 HIGH | **Status**: PLANNED
        patterns = {
            'type': r'\*\*Type\*\*: [🔧📱🔒📊🏗️]?\s*(\w+)',
            'priority': r'\*\*Priority\*\*: [🔴🟠🟡🟢]?\s*(\w+)',
            'status': r'\*\*Status\*\*: (\w+)',
            'phase': r'\*\*Phase\*\*: (\w+)',
            'sp_total': r'\*\*SP Total\*\*: (\d+)',
            'sp_completed': r'\*\*SP Completed\*\*: (\d+)',
            'owner': r'\*\*Owner\*\*: @(\w+)',
            'target_date': r'\*\*Target\*\*: ([\d-]+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, epic_section)
            if match:
                value = match.group(1)
                if key in ['sp_total', 'sp_completed']:
                    metadata[key] = int(value)
                elif key == 'target_date':
                    metadata[key] = datetime.strptime(value, '%Y-%m-%d')
                else:
                    metadata[key] = value

        # Extract description (text after metadata, before features)
        desc_pattern = r'\*\*Dependencies\*\*:.*?\n\n(.+?)(?:\n\n|\n####|$)'
        desc_match = re.search(desc_pattern, epic_section, re.DOTALL)
        if desc_match:
            metadata['description'] = desc_match.group(1).strip()

        return metadata

    def _parse_features(self, section: str, parent_epic_id: str) -> List[Dict]:
        """Extract features nested under an epic"""
        features = []

        # Match: #### FEATURE-001 | Title
        feature_pattern = r'#### (FEATURE-\d+) \| (.+?)$'

        for match in re.finditer(feature_pattern, section, re.MULTILINE):
            feature_id = match.group(1)
            feature_title = match.group(2)

            feature_data = self._extract_feature_metadata(section, feature_id)
            feature_data['id'] = feature_id
            feature_data['title'] = feature_title
            feature_data['type'] = 'feature'
            feature_data['parent_id'] = parent_epic_id

            # Extract nested stories
            feature_data['stories'] = self._parse_stories(section, feature_id)

            features.append(feature_data)

        return features

    def _parse_stories(self, section: str, parent_feature_id: str) -> List[Dict]:
        """Extract stories nested under a feature"""
        stories = []

        # Match: ##### STORY-001 | Title
        story_pattern = r'##### (STORY-\d+) \| (.+?)$'

        for match in re.finditer(story_pattern, section, re.MULTILINE):
            story_id = match.group(1)
            story_title = match.group(2)

            story_data = self._extract_story_metadata(section, story_id)
            story_data['id'] = story_id
            story_data['title'] = story_title
            story_data['type'] = 'story'
            story_data['parent_id'] = parent_feature_id

            stories.append(story_data)

        return stories

    # ... (similar methods for feature and story metadata extraction)
```

### 3.2 Markdown Generator

**Purpose:** Generate project.md from database records

**Technology:** Jinja2 templates for markdown generation

**Template: project_template.md.j2**

```jinja2
# Project Manager

<!-- Config: Last Epic ID: {{ config.last_epic_id }}, Last Feature ID: {{ config.last_feature_id }}, Last Story ID: {{ config.last_story_id }}, Last Task ID: {{ config.last_task_id }} -->

## ⚙️ Configuration

**Hierarchy**: Epic > Feature > Story > Task
**Columns**: 📋 PLANNED (planned) | 🚀 IN PROGRESS (in-progress) | 🧪 TESTING (testing) | ✅ COMPLETED (completed)
**Priorities**: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW
**Types**: 📱 FUNCTIONAL, 🔧 TECHNICAL, 🔒 COMPLIANCE, 📊 REPORTING, 🏗️ INFRASTRUCTURE
**Phases**: INITIATIE, REALISATIE, IMPLEMENTATIE
**Users**: {% for user in users %}@{{ user.username }} ({{ user.name }}){% if not loop.last %}, {% endif %}{% endfor %}
**Tags**: {{ tags | join(', ') }}

---

{% for status in ['PLANNED', 'IN PROGRESS', 'TESTING', 'COMPLETED'] %}
## {{ status_icons[status] }} {{ status }}

{% for epic in epics_by_status[status] %}
### {{ epic.id }} | {{ epic.title }}
**Type**: {{ type_icons[epic.type] }} {{ epic.type }} | **Priority**: {{ priority_icons[epic.priority] }} {{ epic.priority }} | **Status**: {{ epic.status }} | **Phase**: {{ epic.phase }}
**SP Total**: {{ epic.sp_total }} | **SP Completed**: {{ epic.sp_completed }} | **Progress**: {{ epic.progress }}%
**Owner**: @{{ epic.owner }} | **Target**: {{ epic.target_date.strftime('%Y-%m-%d') if epic.target_date else 'TBD' }}
**Dependencies**: [{% for dep in epic.dependencies %}{{ dep }}{% if not loop.last %}, {% endif %}{% endfor %}]

{{ epic.description }}

{% if epic.business_value %}
**Business Value**: {{ epic.business_value }}
{% endif %}

{% for feature in epic.features %}
#### {{ feature.id }} | {{ feature.title }}
**Parent**: {{ epic.id }} | **Type**: Feature
**SP Total**: {{ feature.sp_total }} | **SP Completed**: {{ feature.sp_completed }} | **Status**: {{ feature.status }}
**Priority**: {{ priority_icons[feature.priority] }} {{ feature.priority }} | **Estimated Sprints**: {{ feature.estimated_sprints }}

{{ feature.description }}

{% for story in feature.stories %}
##### {{ story.id }} | {{ story.title }}
**Parent**: {{ feature.id }} | **Type**: Story
**SP**: {{ story.sp }} | **Sprint**: {{ story.sprint }} | **Status**: {{ story.status }}
**Assigned**: @{{ story.assigned_to }} | **Tags**: {{ story.tags | join(' ') }}

{{ story.description }}

{% if story.acceptance_criteria %}
**Acceptance Criteria**:
{% for criterion in story.acceptance_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

{% if story.subtasks %}
**Subtasks**:
{% for subtask in story.subtasks %}
- [{{ 'x' if subtask.completed else ' ' }}] {{ subtask.description }} ({{ subtask.estimated_hours }}h)
{% endfor %}
{% endif %}

{% endfor %}
{% endfor %}
{% endfor %}

{% endfor %}
```

### 3.3 File Watcher

**Purpose:** Detect changes to markdown files and trigger sync

**Technology:** Watchdog (Python library)

**Implementation:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class ProjectMarkdownHandler(FileSystemEventHandler):
    """Watch for changes to project.md"""

    def __init__(self, sync_engine):
        self.sync_engine = sync_engine
        self.last_modified = {}

    def on_modified(self, event):
        if event.src_path.endswith('project.md'):
            # Debounce: Ignore rapid successive changes (e.g., autosave)
            current_time = time.time()
            last_mod = self.last_modified.get(event.src_path, 0)

            if current_time - last_mod > 2:  # 2 second debounce
                self.last_modified[event.src_path] = current_time
                print(f"Detected change in {event.src_path}")
                self.sync_engine.sync_from_markdown(event.src_path)

# Usage
if __name__ == '__main__':
    from sync_engine import SyncEngine

    sync_engine = SyncEngine(database_url="postgresql+asyncpg://...")
    event_handler = ProjectMarkdownHandler(sync_engine)

    observer = Observer()
    observer.schedule(event_handler, path='/home/eddie/Projects/MarkdownTaskManager', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
```

### 3.4 Conflict Resolution

**Problem:** What if markdown and database are edited simultaneously?

**Solution: Last-Write-Wins with Conflict Detection**

```python
class SyncEngine:
    """Bidirectional sync between markdown and database"""

    async def sync_from_markdown(self, file_path: str):
        """Markdown → Database sync"""
        # Parse markdown
        parser = ProjectMarkdownParser()
        parsed_data = parser.parse_file(file_path)

        # Compare with database
        for epic in parsed_data['epics']:
            db_epic = await self.get_epic_from_db(epic['id'])

            if db_epic is None:
                # New epic in markdown → Create in database
                await self.create_epic_in_db(epic)
            else:
                # Existing epic → Check for conflicts
                if self._has_conflict(db_epic, epic):
                    # Conflict detected → Create conflict record
                    await self.log_conflict(db_epic, epic)
                    # Apply last-write-wins strategy
                    if self._markdown_is_newer(file_path, db_epic.updated_at):
                        await self.update_epic_in_db(epic)
                    # Else: keep database version
                else:
                    # No conflict → Update database
                    await self.update_epic_in_db(epic)

    async def sync_from_database(self):
        """Database → Markdown sync"""
        # Fetch all epics from database
        epics = await self.get_all_epics_from_db()

        # Generate markdown
        generator = MarkdownGenerator()
        markdown_content = generator.generate_project_md(epics)

        # Write to file (with backup)
        backup_path = 'project.md.backup'
        shutil.copy('project.md', backup_path)

        with open('project.md', 'w') as f:
            f.write(markdown_content)

    def _has_conflict(self, db_record: Dict, md_record: Dict) -> bool:
        """Detect if markdown and database have diverged"""
        # Compare critical fields
        critical_fields = ['title', 'status', 'sp', 'assigned_to']

        for field in critical_fields:
            if db_record.get(field) != md_record.get(field):
                return True

        return False

    def _markdown_is_newer(self, file_path: str, db_updated_at: datetime) -> bool:
        """Check if markdown file is newer than database record"""
        file_mtime = os.path.getmtime(file_path)
        file_datetime = datetime.fromtimestamp(file_mtime)

        return file_datetime > db_updated_at
```

---

## 4. Integration Roadmap

### Phase 1: Foundation (Week 1)

**Goal:** Basic sync working (markdown → database)

**Tasks:**
1. ✅ Backend already built
2. Build markdown parser
   - Parse config section
   - Parse epics with metadata
   - Parse nested features/stories/tasks
   - Unit tests for parser
3. Implement sync_from_markdown()
   - Read project.md
   - Parse structure
   - Insert into PostgreSQL
   - Handle nested relationships
4. Test with example-project/project.md

**Success Criteria:**
- ✅ Parse example-project/project.md successfully
- ✅ All epics/features/stories imported to PostgreSQL
- ✅ Hierarchical relationships preserved
- ✅ Metadata (SP, status, assigned_to) imported correctly

### Phase 2: Bidirectional Sync (Week 2)

**Goal:** Database changes write back to markdown

**Tasks:**
1. Build markdown generator
   - Create Jinja2 template
   - Generate markdown from database records
   - Preserve formatting and structure
2. Implement sync_from_database()
   - Fetch all items from database
   - Generate markdown
   - Write to project.md
3. Add file watcher
   - Use Watchdog library
   - Detect changes to project.md
   - Trigger sync_from_markdown()
4. Test bidirectional sync
   - Edit project.md → Check database updated
   - Edit via API → Check project.md updated

**Success Criteria:**
- ✅ Changes in project.md reflect in database
- ✅ Changes via API reflect in project.md
- ✅ File watcher detects edits within 2 seconds
- ✅ Formatting preserved (emoji, indentation)

### Phase 3: Conflict Resolution (Week 3)

**Goal:** Handle simultaneous edits gracefully

**Tasks:**
1. Implement conflict detection
   - Compare markdown vs database
   - Identify diverged fields
2. Add conflict logging
   - Log conflicts to database table
   - Notify via WebSocket
3. Implement resolution strategies
   - Last-write-wins (default)
   - Manual merge (for critical conflicts)
4. Add conflict UI
   - Show conflicts in project-manager.html
   - Allow user to choose version

**Success Criteria:**
- ✅ Conflicts detected and logged
- ✅ Last-write-wins strategy works
- ✅ No data loss during conflicts
- ✅ User notified of conflicts

### Phase 4: Agent Integration (Week 4)

**Goal:** Agents can read/write to markdown and database

**Tasks:**
1. Create agent markdown interface
   - Agents read from database (fast queries)
   - Agents write to database
   - Sync engine updates markdown
2. Test agent workflows
   - Estimation Engine: Calculate SP, write to database, check markdown updated
   - Feature Architect: Create epic breakdown, validate in project.md
3. Add agent activity logging
   - Log agent actions to markdown (comments)
   - Track who made changes (agent vs human)

**Success Criteria:**
- ✅ Agents can create epics/features/stories
- ✅ Agent changes appear in project.md
- ✅ Agent attribution tracked
- ✅ No conflicts between agents and humans

### Phase 5: Real-Time Dashboard (Week 5-6)

**Goal:** Live updates in project-manager.html

**Tasks:**
1. Add WebSocket to FastAPI
   - Broadcast on database changes
   - Event types: ItemCreated, ItemUpdated, ItemDeleted
2. Enhance project-manager.html
   - WebSocket client connection
   - Auto-refresh on events
   - Show "live" indicator
3. Add agent activity dashboard
   - Show running agents
   - Display progress indicators
   - Real-time task updates

**Success Criteria:**
- ✅ Changes appear in UI without refresh
- ✅ Multiple users see updates in real-time
- ✅ Agent activity visible in dashboard
- ✅ Smooth UX (no flickering)

---

## 5. Benefits of This Approach

### For Humans

1. **Familiar Interface** - Keep using project-manager.html
2. **Git-Friendly** - Version control, diffs, branches work
3. **No Lock-In** - Markdown files are portable
4. **Offline Capable** - Edit project.md even without backend running
5. **Text Editor Support** - Use vim, VSCode, any text editor

### For Agents

1. **Structured Queries** - Database enables complex queries
2. **Fast Access** - No need to parse markdown every time
3. **Relational Data** - Join epics/features/stories easily
4. **Analytics** - Calculate metrics (velocity, burndown)
5. **Work Queue** - Agents pull tasks from database

### For the System

1. **Best of Both Worlds** - Human-friendly markdown + Agent-friendly database
2. **Scalability** - Database handles large projects
3. **Collaboration** - Multiple users via API
4. **Extensibility** - Easy to add new features (webhooks, integrations)
5. **Observability** - Track changes, audit logs

---

## 6. Technical Decisions

### Why Markdown as Source of Truth?

**Pros:**
- ✅ Human-readable and editable
- ✅ Git version control (diffs, branches, merges)
- ✅ Portable (no lock-in)
- ✅ Can work offline
- ✅ Simple backup (just copy .md files)

**Cons:**
- ❌ Parsing complexity
- ❌ Conflict resolution needed
- ❌ No referential integrity (database constraint)

**Decision:** Markdown as source of truth is worth the trade-offs for this use case.

### Why Not Database as Source of Truth?

**Pros of DB-first:**
- ✅ Referential integrity
- ✅ ACID transactions
- ✅ No parsing needed
- ✅ Better for complex queries

**Cons of DB-first:**
- ❌ Not human-editable (need UI)
- ❌ Harder to version control
- ❌ Lock-in to specific database
- ❌ Requires backend to edit

**Decision:** Database is secondary store for agent access, not primary.

### Why Both?

**Best of both worlds:**
- Markdown for human editing and version control
- Database for agent queries and analytics
- Sync engine bridges the gap

---

## 7. Example Usage Scenarios

### Scenario 1: Human Creates New Epic

**Flow:**
1. User opens project-manager.html
2. Clicks "New Epic"
3. Fills form: Title, Description, Priority
4. Saves → POST /api/epics
5. Backend creates in PostgreSQL
6. Sync engine writes to project.md
7. Git detects change (optional auto-commit)
8. WebSocket broadcast to all clients

**Result:** Epic exists in both project.md and database

### Scenario 2: Agent Estimates Story Points

**Flow:**
1. User creates STORY-001 (no SP assigned)
2. Agent (Estimation Engine) triggers
3. Agent reads story from database
4. Agent calculates SP = 5 (based on complexity)
5. Agent updates database: STORY-001.sp = 5
6. Sync engine updates project.md
7. WebSocket broadcast
8. User sees "SP: 5" in project-manager.html

**Result:** Automated estimation without human intervention

### Scenario 3: User Edits project.md Directly

**Flow:**
1. User runs: `vim project.md`
2. Changes STORY-001 status from PLANNED → IN PROGRESS
3. Saves file
4. File watcher detects change
5. Sync engine parses project.md
6. Updates database: STORY-001.status = 'IN PROGRESS'
7. WebSocket broadcast
8. project-manager.html auto-refreshes
9. Story moves to "IN PROGRESS" column

**Result:** Direct markdown edits sync to database and UI

### Scenario 4: Multiple Agents Collaborate

**Flow:**
1. User creates FEATURE-001
2. Feature Architect agent breaks down into stories
   - Creates STORY-001, STORY-002, STORY-003
3. Estimation Engine estimates each story
   - STORY-001: 5 SP
   - STORY-002: 8 SP
   - STORY-003: 3 SP
4. Test Engineer creates test tasks
   - STORY-001 → TASK-001: Write unit tests (2 SP)
5. All changes written to database
6. Sync engine updates project.md (one atomic write)
7. project.md now has complete breakdown

**Result:** Agents collaborate to create work breakdown

---

## 8. Next Steps

### Immediate (This Week)

1. **Build Markdown Parser** - Parse project.md into Python objects
2. **Implement sync_from_markdown()** - Import project.md to PostgreSQL
3. **Test with example-project** - Validate parsing and import
4. **Add file watcher** - Auto-sync on file changes

### Week 2

5. **Build Markdown Generator** - Generate project.md from database
6. **Implement sync_from_database()** - Export database to project.md
7. **Test bidirectional sync** - Verify changes in both directions
8. **Document sync behavior** - Update README with sync details

### Week 3

9. **Add conflict detection** - Log conflicts between markdown and database
10. **Implement last-write-wins** - Resolve conflicts automatically
11. **Add conflict UI** - Show conflicts in project-manager.html
12. **Test edge cases** - Simultaneous edits, large files, corrupted markdown

### Week 4

13. **Integrate agents** - Agents write to database, sync to markdown
14. **Test agent workflows** - Verify agent changes appear in project.md
15. **Add agent attribution** - Track which agent made changes
16. **Performance testing** - Sync 100+ epics, test latency

---

## 9. Success Metrics

### Technical Metrics

- **Sync Latency** - Target: <1 second from file change to database update
- **Parse Success Rate** - Target: 100% of valid markdown files parsed correctly
- **Conflict Rate** - Target: <1% of edits result in conflicts
- **Data Integrity** - Target: 0 data loss events

### User Experience Metrics

- **Edit Success Rate** - Target: 100% of user edits saved correctly
- **UI Responsiveness** - Target: Real-time updates within 500ms
- **Agent Attribution** - Target: 100% of agent edits attributed correctly
- **User Satisfaction** - Target: 4.5/5 stars on usability

### System Health Metrics

- **Uptime** - Target: 99.9% availability
- **Error Rate** - Target: <0.1% of sync operations fail
- **Performance** - Target: Handle 10,000 items without slowdown
- **Storage Efficiency** - Target: Database size <2x markdown size

---

## Appendix: Example project.md Structure

See `project.md` in this repository for the complete structure. Key elements:

1. **Config Comment** - Stores last ID counters
2. **Configuration Section** - Defines columns, priorities, users, tags
3. **Status Sections** - PLANNED, IN PROGRESS, TESTING, COMPLETED
4. **Hierarchical Items**:
   - `### EPIC-###` with metadata (Type, Priority, SP Total, Owner, Target)
   - `#### FEATURE-###` nested under epics
   - `##### STORY-###` nested under features
   - Subtasks as checkboxes under stories

**Key Insight:** This structure is PERFECT for agent parsing and generation!

---

**End of Document**
