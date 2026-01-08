# Fase 5: Quality Gates Configuration UI - Design Document

**Datum:** 2025-11-24
**Week:** 48 Dag 4
**Status:** DESIGN PHASE

---

## 1. Overview

### Doel
Een configureerbare UI waar gebruikers quality gates kunnen beheren:
- Checks aan/uit zetten per categorie
- Blocking rules per workflow type instellen
- Thresholds configureren
- Real-time preview van gate configuratie

### Scope
- Nieuwe pagina: `quality-gates-config.html`
- Backend API endpoints voor CRUD operations
- Database tabel voor configuratie persistentie

---

## 2. UI Wireframes

### 2.1 Main Layout

```
+------------------------------------------------------------------+
| QUALITY GATES CONFIGURATION                    [Save] [Reset]     |
+------------------------------------------------------------------+
|                                                                   |
| +---------------------------+  +--------------------------------+ |
| | CATEGORIES                |  | WORKFLOW RULES                 | |
| |                           |  |                                | |
| | [x] SIG-TOP-10 (3)       |  | NEW_FEATURE:                   | |
| |     Target: [90]%        |  |   Block: [Critical] [High]     | |
| |                           |  |   Coverage: [80]%              | |
| | [x] SOLID (3)            |  |                                | |
| |     Target: [85]%        |  | MAINTENANCE:                   | |
| |                           |  |   Block: [Critical]            | |
| | [x] GRASP (2)            |  |   Coverage: [70]%              | |
| |     Target: [85]%        |  |                                | |
| |                           |  | BUG:                           | |
| | [x] TDD (3)              |  |   Block: [Critical]            | |
| |     Target: [80]%        |  |   Regression: [Required]       | |
| |                           |  |                                | |
| | [x] Testing Patterns (6) |  | QUALITY_AUDIT:                 | |
| |     Target: [80]%        |  |   Block: [None - Report Only]  | |
| |                           |  |                                | |
| | [x] Design Patterns (5)  |  | MIGRATION:                     | |
| |     Target: [85]%        |  |   Block: [Critical]            | |
| |                           |  |   E2E: [Required]              | |
| | [x] Clean Code (5)       |  |                                | |
| |     Target: [85]%        |  | REFACTORING:                   | |
| |                           |  |   Block: [Crit] [High] [Med]   | |
| | [x] Law of Demeter (1)   |  |   Target: [85]%                | |
| |     Target: [90]%        |  +--------------------------------+ |
| +---------------------------+                                     |
|                                                                   |
| +---------------------------------------------------------------+ |
| | INDIVIDUAL CHECKS                                              | |
| +---------------------------------------------------------------+ |
| | Category: [All v]  Status: [All v]  Search: [___________]     | |
| |                                                                | |
| | +-----------------------------------------------------------+ | |
| | | Check Name              | Category    | Severity | Status | | |
| | |-------------------------|-------------|----------|--------| | |
| | | Cyclomatic Complexity   | SIG-TOP-10  | Critical | [x] On | | |
| | | Code Duplication        | SIG-TOP-10  | High     | [x] On | | |
| | | Parameter Count         | SIG-TOP-10  | Medium   | [x] On | | |
| | | Single Responsibility   | SOLID       | High     | [x] On | | |
| | | Open-Closed Principle   | SOLID       | Medium   | [x] On | | |
| | | ...                     | ...         | ...      | ...    | | |
| | +-----------------------------------------------------------+ | |
| +---------------------------------------------------------------+ |
|                                                                   |
| +---------------------------------------------------------------+ |
| | PREVIEW                                                        | |
| +---------------------------------------------------------------+ |
| | Current Config Summary:                                        | |
| | - 28/28 checks enabled                                         | |
| | - 8/8 categories active                                        | |
| | - NEW_FEATURE: Blocks Critical + High (80% coverage)          | |
| | - Last saved: 2025-11-24 14:30                                | |
| +---------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### 2.2 Category Configuration Panel

```
+------------------------------------------+
| SIG-TOP-10 MAINTAINABILITY               |
+------------------------------------------+
| Status: [x] Enabled                       |
| Target Score: [90]%                       |
|                                          |
| Checks (3):                              |
| +--------------------------------------+ |
| | [x] Cyclomatic Complexity            | |
| |     Max: [10]  Severity: Critical    | |
| +--------------------------------------+ |
| | [x] Code Duplication                 | |
| |     Max: [5]%  Severity: High        | |
| +--------------------------------------+ |
| | [x] Parameter Count                  | |
| |     Max: [4]   Severity: Medium      | |
| +--------------------------------------+ |
|                                          |
| [Expand All] [Collapse All]              |
+------------------------------------------+
```

### 2.3 Workflow Rules Panel

```
+------------------------------------------+
| NEW_FEATURE WORKFLOW                      |
+------------------------------------------+
| Description: New feature development      |
|                                          |
| Blocking Severities:                     |
| [x] Critical  [x] High  [ ] Medium  [ ] Low |
|                                          |
| Requirements:                            |
| [x] Unit Test Coverage: [80]%            |
| [ ] E2E Test Required                    |
| [ ] Regression Test Required             |
| [x] Documentation Required               |
|                                          |
| Max Iterations: [3]                      |
| Stop on First Failure: [x]               |
+------------------------------------------+
```

---

## 3. API Endpoint Design

### 3.1 Configuration Endpoints

```yaml
# GET /api/quality/config
# Returns current quality gates configuration
Response:
  categories:
    - id: "sig-top-10"
      name: "SIG-TOP-10 Maintainability"
      enabled: true
      target_score: 90
      checks:
        - id: "cyclomatic-complexity"
          name: "Cyclomatic Complexity"
          enabled: true
          severity: "critical"
          threshold: 10
        - id: "code-duplication"
          name: "Code Duplication"
          enabled: true
          severity: "high"
          threshold: 5
  workflow_rules:
    - workflow_type: "NEW_FEATURE"
      blocking_severities: ["critical", "high"]
      required_coverage: 80
      e2e_required: false
      regression_required: false
      max_iterations: 3

# PUT /api/quality/config
# Update full configuration
Request Body: (same structure as GET response)

# PATCH /api/quality/config/category/{category_id}
# Update single category
Request Body:
  enabled: true
  target_score: 85

# PATCH /api/quality/config/check/{check_id}
# Update single check
Request Body:
  enabled: true
  severity: "high"
  threshold: 15

# PATCH /api/quality/config/workflow/{workflow_type}
# Update workflow rules
Request Body:
  blocking_severities: ["critical"]
  required_coverage: 70

# POST /api/quality/config/reset
# Reset to defaults
Response:
  message: "Configuration reset to defaults"
  config: { ... }

# GET /api/quality/config/history
# Configuration change history
Response:
  changes:
    - timestamp: "2025-11-24T14:30:00Z"
      user: "admin"
      change_type: "category_update"
      details: { category: "sig-top-10", field: "target_score", old: 90, new: 85 }
```

### 3.2 Validation Endpoints

```yaml
# POST /api/quality/config/validate
# Validate configuration before saving
Request Body: (full config)
Response:
  valid: true
  warnings:
    - "LOW coverage threshold (60%) for NEW_FEATURE may reduce code quality"
  errors: []

# POST /api/quality/config/preview
# Preview impact of configuration change
Request Body:
  config: { ... }
  test_files: ["src/app.ts", "src/utils.ts"]
Response:
  current_result:
    passed: true
    score: 87
  new_result:
    passed: false
    score: 72
    blocking_issues: 3
```

---

## 4. Database Schema Design

### 4.1 New Tables

```sql
-- Quality Gate Configuration (main config per project)
CREATE TABLE quality_gate_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name VARCHAR(100) NOT NULL DEFAULT 'default',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    UNIQUE(project_id, name)
);

-- Category Configuration
CREATE TABLE quality_category_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES quality_gate_configs(id) ON DELETE CASCADE,
    category_id VARCHAR(50) NOT NULL,  -- 'sig-top-10', 'solid', etc.
    enabled BOOLEAN DEFAULT true,
    target_score INTEGER DEFAULT 80 CHECK (target_score >= 0 AND target_score <= 100),
    UNIQUE(config_id, category_id)
);

-- Individual Check Configuration
CREATE TABLE quality_check_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES quality_gate_configs(id) ON DELETE CASCADE,
    check_id VARCHAR(100) NOT NULL,  -- 'cyclomatic-complexity'
    category_id VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    threshold_value FLOAT,  -- Configurable threshold
    threshold_type VARCHAR(20),  -- 'max', 'min', 'percentage'
    UNIQUE(config_id, check_id)
);

-- Workflow Rules Configuration
CREATE TABLE quality_workflow_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES quality_gate_configs(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,  -- 'NEW_FEATURE', 'BUG', etc.
    blocking_severities TEXT[] DEFAULT ARRAY['critical'],
    required_coverage INTEGER DEFAULT 80,
    e2e_required BOOLEAN DEFAULT false,
    regression_required BOOLEAN DEFAULT false,
    documentation_required BOOLEAN DEFAULT false,
    max_iterations INTEGER DEFAULT 3,
    stop_on_first_failure BOOLEAN DEFAULT true,
    UNIQUE(config_id, workflow_type)
);

-- Configuration Change History (audit log)
CREATE TABLE quality_config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES quality_gate_configs(id) ON DELETE CASCADE,
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(100),
    change_type VARCHAR(50) NOT NULL,  -- 'category_update', 'check_update', 'workflow_update', 'reset'
    entity_type VARCHAR(50),  -- 'category', 'check', 'workflow'
    entity_id VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    comment TEXT
);

-- Indexes for performance
CREATE INDEX idx_category_configs_config ON quality_category_configs(config_id);
CREATE INDEX idx_check_configs_config ON quality_check_configs(config_id);
CREATE INDEX idx_check_configs_category ON quality_check_configs(category_id);
CREATE INDEX idx_workflow_rules_config ON quality_workflow_rules(config_id);
CREATE INDEX idx_config_history_config ON quality_config_history(config_id);
CREATE INDEX idx_config_history_changed_at ON quality_config_history(changed_at);
```

### 4.2 Default Data

```sql
-- Insert default categories
INSERT INTO quality_category_configs (config_id, category_id, enabled, target_score)
VALUES
    (:config_id, 'sig-top-10', true, 90),
    (:config_id, 'solid', true, 85),
    (:config_id, 'grasp', true, 85),
    (:config_id, 'tdd', true, 80),
    (:config_id, 'testing-patterns', true, 80),
    (:config_id, 'design-patterns', true, 85),
    (:config_id, 'clean-code', true, 85),
    (:config_id, 'law-of-demeter', true, 90);

-- Insert default workflow rules
INSERT INTO quality_workflow_rules (config_id, workflow_type, blocking_severities, required_coverage)
VALUES
    (:config_id, 'NEW_FEATURE', ARRAY['critical', 'high'], 80),
    (:config_id, 'MAINTENANCE', ARRAY['critical'], 70),
    (:config_id, 'BUG', ARRAY['critical'], 70),
    (:config_id, 'QUALITY_AUDIT', ARRAY[]::TEXT[], 0),
    (:config_id, 'MIGRATION', ARRAY['critical'], 65),
    (:config_id, 'REFACTORING', ARRAY['critical', 'high', 'medium'], 85),
    (:config_id, 'DOCUMENTATION', ARRAY[]::TEXT[], 0),
    (:config_id, 'HOTFIX', ARRAY['critical'], 60);
```

---

## 5. Component Structure

### 5.1 File Layout

```
frontend/
├── quality-gates-config.html      # Main configuration page
├── css/
│   └── quality-gates-config.css   # Styles (or embedded)
└── js/
    └── quality-gates-config.js    # Logic (or embedded)

backend/
├── app/
│   ├── api/
│   │   └── quality_config.py      # New API router
│   ├── models/
│   │   └── quality_config.py      # SQLAlchemy models
│   ├── schemas/
│   │   └── quality_config.py      # Pydantic schemas
│   └── services/
│       └── quality_config_service.py  # Business logic
├── alembic/
│   └── versions/
│       └── 010_add_quality_config_tables.py  # Migration
```

### 5.2 Frontend Components

```javascript
// Component structure (vanilla JS)
const QualityGatesConfig = {
    // State
    state: {
        config: null,
        isDirty: false,
        selectedCategory: null,
        searchFilter: '',
    },

    // Components
    components: {
        CategoryPanel: { /* ... */ },
        WorkflowRulesPanel: { /* ... */ },
        ChecksTable: { /* ... */ },
        PreviewPanel: { /* ... */ },
        SaveControls: { /* ... */ },
    },

    // API
    api: {
        getConfig: () => fetch('/api/quality/config').then(r => r.json()),
        saveConfig: (config) => fetch('/api/quality/config', { method: 'PUT', body: JSON.stringify(config) }),
        resetConfig: () => fetch('/api/quality/config/reset', { method: 'POST' }),
        validateConfig: (config) => fetch('/api/quality/config/validate', { method: 'POST', body: JSON.stringify(config) }),
    },

    // Event handlers
    handlers: {
        onCategoryToggle: (categoryId, enabled) => { /* ... */ },
        onCheckToggle: (checkId, enabled) => { /* ... */ },
        onThresholdChange: (checkId, value) => { /* ... */ },
        onWorkflowRuleChange: (workflow, rule, value) => { /* ... */ },
        onSave: () => { /* ... */ },
        onReset: () => { /* ... */ },
    },
};
```

---

## 6. Implementation Plan

### Week 49 - Implementation

| Day | Task | Output |
|-----|------|--------|
| 1 | Database migration + models | `010_add_quality_config_tables.py` |
| 2 | API endpoints + service | `quality_config.py` (API + service) |
| 3 | Frontend HTML structure | `quality-gates-config.html` |
| 4 | Frontend JS + interactions | Working config UI |
| 5 | Testing + integration | E2E tests, bug fixes |

### Dependencies

- `backend/app/api/quality_dashboard.py` - Existing quality API
- `ARCHITECTURE.md` - Quality Gates System spec
- Database: PostgreSQL with existing schema

---

## 7. Success Criteria

- [ ] All 8 categories configurable via UI
- [ ] All 28 checks individually toggleable
- [ ] Workflow rules for 8 workflow types
- [ ] Configuration persisted to database
- [ ] Change history tracked
- [ ] Preview functionality works
- [ ] Reset to defaults works
- [ ] Responsive design (mobile-friendly)

---

## 8. Open Questions

1. **Multi-project support?** - Should each project have its own config?
   - Recommendation: Yes, with ability to clone configs

2. **Role-based access?** - Who can modify configuration?
   - Recommendation: Admin-only for now, add RBAC later

3. **Import/Export?** - Allow config sharing between projects?
   - Recommendation: Yes, JSON export/import

---

**Next Step:** Database migration (Week 49 Day 1)
