# Configuration and Customization

> **[Back to README](../README.md)**

Guide to customizing your Multi-Stack AI Agent Platform setup.

---

## Kanban Columns

Customize your columns in `kanban.md`:

```markdown
**Columns**: Backlog (backlog) | Analysis (analysis) | Dev (dev) | Review (review) | Done (done)
```

**Format:** `Emoji Name (id) | ...`

**Examples:**
- **Simple development:** `To Do | In Progress | Done`
- **Scrum:** `Backlog | Sprint | In Progress | Review | Done`
- **Extended Kanban:** `Icebox | Backlog | Analysis | Dev | QA | Deploy | Done`

---

## Categories

Define your project categories:

```markdown
**Categories**: Frontend, Backend, Database, DevOps, Design, Tests, Documentation
```

**Adapt to your context:**
- **Web:** `UI, API, Database, DevOps`
- **Mobile:** `iOS, Android, Backend, Design`
- **Data:** `ETL, Analysis, ML, Visualization`

---

## Users

List team members:

```markdown
**Users**: @alice (Alice Martin), @bob (Bob Smith), @charlie (Charlie Brown)
```

**Format:** `@username (Full Name)`

---

## Tags

Create an adapted tag system:

```markdown
**Tags**: #bug, #feature, #refactor, #docs, #urgent, #blocked, #tech-debt
```

**Examples of tag systems:**

| System | Tags |
|--------|------|
| **By type** | `#bug`, `#feature`, `#refactor`, `#docs` |
| **By priority** | `#urgent`, `#important`, `#nice-to-have` |
| **By status** | `#blocked`, `#waiting`, `#in-review` |
| **By domain** | `#security`, `#performance`, `#ux`, `#a11y` |

---

## Complete Configuration Example

```markdown
# Kanban Board

<!-- Config: Last Task ID: 42 -->

## Configuration

**Columns**: Backlog (backlog) | Sprint (sprint) | In Progress (in-progress) | Review (review) | Done (done)
**Categories**: Frontend, Backend, API, Database, DevOps, Testing
**Users**: @alice (Alice Martin), @bob (Bob Smith), @charlie (Charlie Brown)
**Tags**: #bug, #feature, #refactor, #docs, #urgent, #blocked, #security, #performance

---

## Backlog

## Sprint

## In Progress

## Review

## Done
```

---

## Tips

### Consistent naming
- Use lowercase for IDs: `(in-progress)` not `(In-Progress)`
- Keep tag names short: `#bug` not `#bug-report`
- Use @username format for all users

### Team conventions
- Document your tag meanings in `AI_WORKFLOW.md`
- Agree on priority levels with the team
- Keep categories aligned with your tech stack

### Performance
- Avoid too many columns (5-7 is optimal)
- Archive completed tasks regularly
- Use tags instead of creating new columns for temporary states

---

**[Back to README](../README.md)** | **[Features](./FEATURES.md)** | **[Use Cases](./USE_CASES.md)**
