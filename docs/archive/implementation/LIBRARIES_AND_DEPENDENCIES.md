# Libraries and Dependencies - Conditional Tracking voor Alle Levels

## 🎯 Probleem

Je vraag: "libraries are conditional voor alle epics, features, stories en tasks. hoe kunnen we dat zien"

**Use Case**: Track welke libraries/dependencies nodig zijn op elk niveau:
- **Epic level**: Welke technologieën/frameworks voor hele initiatief?
- **Feature level**: Welke libraries voor deze capability?
- **Story level**: Welke dependencies voor deze story?
- **Task level**: Welke specifieke packages/tools?

**Conditional**: Niet alle children hebben dezelfde dependencies. Sommige stories binnen een feature hebben React, andere Vue, etc.

---

## 📊 Real-World Voorbeelden

### Voorbeeld 1: Frontend Modernization Epic

```
EPIC-001: Frontend Modernization
├── Libraries: React 18, TypeScript 5, Vite 4
├── Conditional: Some features use legacy jQuery
│
├── FEATURE-001: Component Library
│   ├── Libraries: Storybook 7, Jest, Testing Library
│   ├── Conditional: Only UI components, not data layer
│   │
│   ├── STORY-001: Button Component
│   │   ├── Libraries: React, TypeScript
│   │   ├── Dependencies: @emotion/styled
│   │   ├── Conditional: No state management needed
│   │   │
│   │   └── TASK-001: Implement button variants
│   │       ├── Tools: VS Code, Chrome DevTools
│   │       └── Dependencies: @emotion/react@^11.0.0
│   │
│   └── STORY-002: Form Components
│       ├── Libraries: React Hook Form, Zod
│       ├── Conditional: Heavy validation needed
│       └── Dependencies: yup (alternative to Zod)
│
└── FEATURE-002: Data Fetching
    ├── Libraries: React Query, Axios
    ├── Conditional: REST API, no GraphQL yet
    └── STORY-003: API Integration
        ├── Libraries: Axios, React Query
        └── Conditional: Requires auth token
```

### Voorbeeld 2: Backend Microservices Epic

```
EPIC-002: Microservices Migration
├── Libraries: Node.js 20, Docker, Kubernetes
├── Conditional: Java services blijven voor legacy
│
├── FEATURE-003: Authentication Service
│   ├── Libraries: Express, Passport, JWT
│   ├── Database: PostgreSQL 15
│   ├── Conditional: OAuth2 voor sommige endpoints
│   │
│   └── STORY-004: JWT Authentication
│       ├── Libraries: jsonwebtoken@^9.0.0, bcrypt
│       ├── Conditional: Requires Redis voor token cache
│       │
│       └── TASK-002: Setup JWT signing
│           ├── Tools: OpenSSL, Docker
│           └── Dependencies: crypto (Node built-in)
│
└── FEATURE-004: Payment Service
    ├── Libraries: Stripe SDK, Express
    ├── Conditional: PCI compliance requirements
    └── STORY-005: Stripe Integration
        ├── Libraries: stripe@^12.0.0
        ├── Conditional: Webhook handling required
        └── Dependencies: body-parser, helmet
```

---

## 🔧 Implementatie Optie 1: Metadata Fields

### Data Model

**Epic Schema Update:**
```markdown
# EPIC-001 | Frontend Modernization

**Type**: Epic
**Priority**: 🔴 CRITICAL
**Status**: IN_PROGRESS

## Libraries & Dependencies
**Required Libraries**:
- React 18.2.0
- TypeScript 5.0
- Vite 4.3

**Optional Libraries** (conditional):
- jQuery 3.6 (voor legacy components)
- Lodash 4.17 (voor utilities)

**Constraints**:
- Node.js >= 18.0.0
- npm >= 9.0.0

## Conditional Dependencies
**Feature-001 (Component Library)**:
- Storybook 7.0 (alleen voor UI development)
- Jest 29.0 (voor testing)

**Feature-002 (Data Fetching)**:
- React Query 4.0 (voor API calls)
- Axios 1.4 (HTTP client)
```

**Feature Schema Update:**
```markdown
# FEATURE-001 | Component Library

**Type**: Feature
**Status**: IN_PROGRESS

## Libraries & Dependencies
**Inherited from Epic**:
- React 18.2.0 (from EPIC-001)
- TypeScript 5.0 (from EPIC-001)

**Feature-specific**:
- Storybook 7.0.0
- Jest 29.5.0
- @testing-library/react 14.0

**Conditional**:
- @emotion/styled (only for styled components stories)
- Chromatic (only for visual testing)

## Why Conditional?
- Not all stories need Storybook (only UI components)
- Testing libraries only for stories with tests
- Emotion only for styled components, not standard CSS
```

**Story Schema Update:**
```markdown
# STORY-001 | Button Component

**Type**: Story
**Status**: IN_PROGRESS

## Dependencies
**Inherited**:
- React 18.2.0 (from EPIC-001)
- TypeScript 5.0 (from EPIC-001)
- Storybook 7.0 (from FEATURE-001)

**Story-specific**:
- @emotion/react ^11.11.0
- @emotion/styled ^11.11.0

**Dev Dependencies**:
- Jest 29.5.0
- @testing-library/react 14.0

**Conditional**:
- @storybook/addon-a11y (if accessibility testing needed)
- react-icons (if using icon library)

## Installation
\`\`\`bash
npm install @emotion/react @emotion/styled
npm install -D @testing-library/react
\`\`\`
```

**Task Schema Update:**
```markdown
# TASK-001 | Implement button variants

**Type**: Task
**Status**: IN_PROGRESS

## Tools & Dependencies
**Required**:
- @emotion/react ^11.11.0 (for styling)
- TypeScript (for type safety)

**Dev Tools**:
- VS Code
- Chrome DevTools
- React DevTools

**Optional** (conditional):
- Prettier (for code formatting)
- ESLint (for linting)

## Setup Instructions
\`\`\`bash
# Install dependencies
npm install @emotion/react

# Run in development
npm run storybook
\`\`\`
```

---

## 🎨 UI Implementation

### 1. Library Badge Display

In hierarchy cards, show library badges:

```javascript
function createHierarchyCard(item) {
    let librariesHTML = '';

    if (item.libraries && item.libraries.length > 0) {
        librariesHTML = `
            <div class="libraries-section">
                <span class="libraries-label">📚 Libraries:</span>
                ${item.libraries.map(lib => `
                    <span class="library-badge" title="${lib.name} ${lib.version}">
                        ${lib.name}
                    </span>
                `).join('')}
                ${item.conditionalLibraries && item.conditionalLibraries.length > 0 ? `
                    <span class="conditional-indicator" title="Has conditional dependencies">
                        ⚠️ ${item.conditionalLibraries.length} conditional
                    </span>
                ` : ''}
            </div>
        `;
    }

    return `
        <div class="hierarchy-card">
            <div class="card-header">${item.id} | ${item.title}</div>
            <!-- ... other fields ... -->
            ${librariesHTML}
        </div>
    `;
}
```

**Visual Result:**
```
┌─────────────────────────────────────────┐
│ FEATURE-001 | Component Library         │
│ Status: IN_PROGRESS    SP: 13/34       │
│                                         │
│ 📚 Libraries:                           │
│ [React] [TypeScript] [Storybook] [Jest]│
│ ⚠️ 2 conditional                       │
└─────────────────────────────────────────┘
```

### 2. Edit Modal - Libraries Section

Add libraries section to edit modal:

```html
<!-- In itemEditForm -->
<div class="form-section" id="librariesSection">
    <h3>Libraries & Dependencies</h3>

    <!-- Inherited libraries (read-only) -->
    <div class="inherited-libraries">
        <label>Inherited from Parent:</label>
        <div id="inheritedLibrariesList">
            <span class="library-badge inherited">React 18.2</span>
            <span class="library-badge inherited">TypeScript 5.0</span>
        </div>
    </div>

    <!-- Required libraries -->
    <div class="required-libraries">
        <label>Required Libraries:</label>
        <div id="requiredLibrariesList">
            <!-- Existing libraries -->
        </div>
        <button type="button" onclick="addLibrary('required')">+ Add Required Library</button>
    </div>

    <!-- Conditional libraries -->
    <div class="conditional-libraries">
        <label>
            Conditional Libraries:
            <span class="help-text">Libraries only needed for some children</span>
        </label>
        <div id="conditionalLibrariesList">
            <!-- Existing conditional libraries -->
        </div>
        <button type="button" onclick="addLibrary('conditional')">+ Add Conditional Library</button>
    </div>
</div>
```

**Add Library Modal:**
```javascript
async function addLibrary(type) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Add ${type} Library</h2>
            <form id="addLibraryForm">
                <label>Library Name:</label>
                <input type="text" id="libraryName" placeholder="e.g., React" required>

                <label>Version:</label>
                <input type="text" id="libraryVersion" placeholder="e.g., 18.2.0 or ^18.0.0">

                <label>Reason (for conditional):</label>
                <textarea id="libraryReason" placeholder="Why is this conditional?"></textarea>

                <label>Required for:</label>
                <input type="text" id="libraryScope" placeholder="e.g., Only for UI components">

                <button type="submit">Add Library</button>
                <button type="button" onclick="closeLibraryModal()">Cancel</button>
            </form>
        </div>
    `;

    document.body.appendChild(modal);
}
```

### 3. Dependency Visualization

**Hierarchical Dependency Tree:**
```javascript
function renderDependencyTree(epic) {
    const tree = document.getElementById('dependencyTree');

    tree.innerHTML = `
        <div class="dep-tree">
            <div class="dep-node epic">
                <div class="dep-header">
                    ${epic.id} | ${epic.title}
                </div>
                <div class="dep-libraries">
                    ${epic.libraries.map(lib => `
                        <span class="lib-badge">${lib.name} ${lib.version}</span>
                    `).join('')}
                </div>
                <div class="dep-children">
                    ${epic.features.map(feature => renderFeatureDependencies(feature)).join('')}
                </div>
            </div>
        </div>
    `;
}

function renderFeatureDependencies(feature) {
    return `
        <div class="dep-node feature">
            <div class="dep-header">${feature.id}</div>
            <div class="dep-inherited">
                <span class="inherited-label">↓ Inherited:</span>
                ${feature.inheritedLibraries.map(lib => `
                    <span class="lib-badge inherited">${lib.name}</span>
                `).join('')}
            </div>
            <div class="dep-specific">
                <span class="specific-label">+ Feature-specific:</span>
                ${feature.specificLibraries.map(lib => `
                    <span class="lib-badge">${lib.name}</span>
                `).join('')}
            </div>
            ${feature.conditionalLibraries.length > 0 ? `
                <div class="dep-conditional">
                    <span class="conditional-label">⚠️ Conditional:</span>
                    ${feature.conditionalLibraries.map(lib => `
                        <span class="lib-badge conditional" title="${lib.reason}">
                            ${lib.name}
                        </span>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}
```

**Visual Tree:**
```
┌────────────────────────────────────────────────────┐
│ EPIC-001: Frontend Modernization                  │
│ 📚 React 18  TypeScript 5  Vite 4                 │
│                                                    │
│ ├─ FEATURE-001: Component Library                 │
│ │  ↓ Inherited: React, TypeScript                 │
│ │  + Specific: Storybook, Jest                    │
│ │  ⚠️ Conditional: Emotion (only styled stories)  │
│ │                                                  │
│ │  ├─ STORY-001: Button Component                 │
│ │  │  ↓ Inherited: React, TypeScript, Storybook   │
│ │  │  + Specific: @emotion/react                  │
│ │  │                                               │
│ │  └─ STORY-002: Form Components                  │
│ │     ↓ Inherited: React, TypeScript, Storybook   │
│ │     + Specific: React Hook Form, Zod            │
│ │                                                  │
│ └─ FEATURE-002: Data Fetching                     │
│    ↓ Inherited: React, TypeScript                 │
│    + Specific: React Query, Axios                 │
│    ⚠️ Conditional: GraphQL (future migration)     │
└────────────────────────────────────────────────────┘
```

---

## 🔍 Dependency Analysis Features

### 1. "Show All Dependencies" View

Button in header: "📦 Dependencies"

```javascript
async function showDependencyAnalysis() {
    const allItems = await loadAllItems(); // Load entire hierarchy

    const analysis = {
        byLibrary: {},
        byLevel: { epic: {}, feature: {}, story: {}, task: {} },
        conflicts: [],
        unused: []
    };

    // Analyze by library
    allItems.forEach(item => {
        item.libraries?.forEach(lib => {
            if (!analysis.byLibrary[lib.name]) {
                analysis.byLibrary[lib.name] = {
                    name: lib.name,
                    versions: new Set(),
                    usedIn: []
                };
            }
            analysis.byLibrary[lib.name].versions.add(lib.version);
            analysis.byLibrary[lib.name].usedIn.push(item);
        });
    });

    // Check version conflicts
    Object.values(analysis.byLibrary).forEach(lib => {
        if (lib.versions.size > 1) {
            analysis.conflicts.push({
                library: lib.name,
                versions: Array.from(lib.versions),
                items: lib.usedIn
            });
        }
    });

    renderDependencyReport(analysis);
}
```

**Report View:**
```
┌──────────────────────────────────────────────────┐
│ Dependency Analysis Report                       │
├──────────────────────────────────────────────────┤
│                                                  │
│ 📊 Overview:                                     │
│   • Total Libraries: 15                          │
│   • Epics: 3 libraries                           │
│   • Features: 8 libraries                        │
│   • Stories: 12 libraries                        │
│   • Tasks: 5 libraries                           │
│                                                  │
│ ⚠️ Version Conflicts (2):                        │
│   • React: 18.2.0 (EPIC-001), 17.0.2 (STORY-015)│
│   • TypeScript: 5.0 (Epic), 4.9 (FEATURE-003)   │
│                                                  │
│ 📚 Most Used Libraries:                          │
│   1. React - Used in 12 stories                  │
│   2. TypeScript - Used in 10 stories             │
│   3. Jest - Used in 8 stories                    │
│                                                  │
│ 🔍 Conditional Libraries (5):                    │
│   • Storybook (only UI components)              │
│   • Emotion (only styled components)            │
│   • React Query (only data fetching)            │
│   • GraphQL (future migration)                  │
│   • jQuery (legacy support)                     │
│                                                  │
│ [Export to CSV] [Generate package.json]         │
└──────────────────────────────────────────────────┘
```

### 2. Dependency Impact Analysis

When editing a library, show impact:

```javascript
function showDependencyImpact(library, newVersion) {
    const affectedItems = findItemsUsingLibrary(library);

    const modal = document.createElement('div');
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Impact Analysis: ${library} ${newVersion}</h2>

            <div class="impact-summary">
                <p>Updating ${library} will affect:</p>
                <ul>
                    <li>${affectedItems.epics.length} Epics</li>
                    <li>${affectedItems.features.length} Features</li>
                    <li>${affectedItems.stories.length} Stories</li>
                    <li>${affectedItems.tasks.length} Tasks</li>
                </ul>
            </div>

            <div class="affected-items">
                <h3>Affected Items:</h3>
                ${affectedItems.all.map(item => `
                    <div class="affected-item">
                        <span class="item-id">${item.id}</span>
                        <span class="item-title">${item.title}</span>
                        <span class="current-version">${item.libraryVersions[library]}</span>
                        <span class="arrow">→</span>
                        <span class="new-version">${newVersion}</span>
                    </div>
                `).join('')}
            </div>

            <div class="breaking-changes">
                <h3>⚠️ Potential Breaking Changes:</h3>
                <ul>
                    ${getBreakingChanges(library, newVersion).map(change => `
                        <li>${change}</li>
                    `).join('')}
                </ul>
            </div>

            <button onclick="updateAllDependencies('${library}', '${newVersion}')">
                Update All
            </button>
            <button onclick="closeModal()">Cancel</button>
        </div>
    `;

    document.body.appendChild(modal);
}
```

### 3. Generate package.json

Export all dependencies to package.json:

```javascript
async function generatePackageJson(epic) {
    const allDependencies = {};
    const devDependencies = {};

    // Collect all libraries from hierarchy
    const allItems = await loadEpicHierarchy(epic);

    allItems.forEach(item => {
        item.libraries?.forEach(lib => {
            if (lib.dev) {
                devDependencies[lib.name] = lib.version;
            } else {
                allDependencies[lib.name] = lib.version;
            }
        });
    });

    const packageJson = {
        name: epic.id.toLowerCase(),
        version: "1.0.0",
        description: epic.title,
        dependencies: allDependencies,
        devDependencies: devDependencies
    };

    // Download as file
    const blob = new Blob([JSON.stringify(packageJson, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `package.json`;
    a.click();
}
```

---

## 📋 Parser & Serializer Updates

### Parser Extension:
```javascript
function parseEpicFile(content) {
    const epic = {
        // ... existing fields
        libraries: [],
        conditionalLibraries: []
    };

    // Parse libraries section
    const librariesSection = extractSection(content, '## Libraries & Dependencies');
    if (librariesSection) {
        const requiredMatch = librariesSection.match(/\*\*Required Libraries\*\*:\n([\s\S]*?)(?=\n\*\*|$)/);
        if (requiredMatch) {
            epic.libraries = parseLibraryList(requiredMatch[1]);
        }

        const conditionalMatch = librariesSection.match(/\*\*Optional Libraries\*\*.*?:\n([\s\S]*?)(?=\n\*\*|$)/);
        if (conditionalMatch) {
            epic.conditionalLibraries = parseConditionalLibraries(conditionalMatch[1]);
        }
    }

    return epic;
}

function parseLibraryList(text) {
    const lines = text.trim().split('\n');
    return lines
        .map(line => line.trim())
        .filter(line => line.startsWith('-'))
        .map(line => {
            const match = line.match(/- ([^\s]+)\s+([\d.^~]+)?/);
            return match ? {
                name: match[1],
                version: match[2] || 'latest'
            } : null;
        })
        .filter(Boolean);
}

function parseConditionalLibraries(text) {
    const lines = text.trim().split('\n');
    return lines
        .filter(line => line.startsWith('-'))
        .map(line => {
            const match = line.match(/- ([^\s]+)\s+([\d.^~]+)?\s*\((.*?)\)/);
            return match ? {
                name: match[1],
                version: match[2] || 'latest',
                reason: match[3]
            } : null;
        })
        .filter(Boolean);
}
```

### Serializer Extension:
```javascript
function serializeEpic(epic) {
    let md = `# ${epic.id} | ${epic.title}\n\n`;

    // ... existing metadata

    // Libraries section
    if (epic.libraries && epic.libraries.length > 0) {
        md += `## Libraries & Dependencies\n\n`;

        md += `**Required Libraries**:\n`;
        epic.libraries.forEach(lib => {
            md += `- ${lib.name} ${lib.version}\n`;
        });
        md += `\n`;

        if (epic.conditionalLibraries && epic.conditionalLibraries.length > 0) {
            md += `**Optional Libraries** (conditional):\n`;
            epic.conditionalLibraries.forEach(lib => {
                md += `- ${lib.name} ${lib.version} (${lib.reason})\n`;
            });
            md += `\n`;
        }
    }

    // ... rest of serialization

    return md;
}
```

---

## 🎯 Implementation Stappenplan

### Phase 1: Basic Library Tracking (Week 1)
- [ ] Add `libraries` array field to all schemas
- [ ] Add `conditionalLibraries` array field
- [ ] Update parsers to read library sections
- [ ] Update serializers to write library sections
- [ ] Test: Manually add libraries to epic.md

### Phase 2: UI - Display (Week 1)
- [ ] Show library badges in hierarchy cards
- [ ] Show inherited libraries in edit modal (read-only)
- [ ] Add "📚 Libraries" indicator
- [ ] Show conditional library count

### Phase 3: UI - Editing (Week 2)
- [ ] "Add Library" button in edit modal
- [ ] Library add/edit/remove UI
- [ ] Conditional library reason field
- [ ] Inherited libraries display

### Phase 4: Analysis (Week 2)
- [ ] "📦 Dependencies" button in header
- [ ] Dependency analysis report
- [ ] Version conflict detection
- [ ] Most-used libraries report
- [ ] Export to package.json

### Phase 5: Advanced (Week 3)
- [ ] Dependency impact analysis
- [ ] Dependency tree visualization
- [ ] Bulk library update
- [ ] Breaking changes warnings

---

## 💡 Aanbeveling

**Start met Phase 1 & 2** (1 week):
- Simpele library tracking in metadata
- Display in cards (read-only)
- Manual editing in markdown files

**Dan Phase 3** (1 week):
- Edit UI for adding/removing libraries
- Inherited libraries display

**Later Phase 4 & 5** (2 weeks):
- Advanced analysis features
- Dependency graph
- Impact analysis

**Total effort**: 4 weeks voor complete implementation

---

**Datum**: 2025-11-12
**Versie**: 1.0
**Status**: Design Document - Not Yet Implemented
**Priority**: MEDIUM (after Sprint enhancements)
