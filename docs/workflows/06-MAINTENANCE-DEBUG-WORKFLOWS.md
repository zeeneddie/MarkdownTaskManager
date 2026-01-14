# Maintenance & Debug Workflows

## Overview

Workflows for ongoing maintenance, debugging, and quality improvement.

---

## Maintenance Workflow (MAINTENANCE)

**Entry Point**: `/api/workflows/maintenance`

| Step | API | Agent | Input | Output | DB |
|------|-----|-------|-------|--------|-----|
| 1. Scan | POST /maintenance/scan | Marcus | project_path | debt_items | technical_debt |
| 2. Analyze | POST /maintenance/analyze | Quinn | debt_items | prioritized_list | code_analysis |
| 3. Plan | POST /maintenance/plan | SM | priorities | sprint_plan | items |
| 4. Execute | POST /maintenance/execute | DEV | tasks | completed | items |

**Dashboard**: maintenance-scheduler.html

---

## Bug Workflow (BUG)

**Entry Point**: `/api/workflows/bug`

| Step | API | Agent | Input | Output | DB |
|------|-----|-------|-------|--------|-----|
| 1. Triage | POST /bugs/triage | Betty | bug_report | root_cause | bug |
| 2. Reproduce | POST /bugs/reproduce | Tessa | root_cause | test_case | bug |
| 3. Fix | POST /bugs/fix | DEV | test_case | fix | items |
| 4. Verify | POST /bugs/verify | Tessa | fix | regression_tests | bug |

**Dashboard**: kanban-dashboard.html

---

## Quality Audit (QUALITY_AUDIT)

**Entry Point**: `/api/workflows/quality-audit`

| Step | API | Agent | Input | Output | DB |
|------|-----|-------|-------|--------|-----|
| 1. Scan | POST /quality/scan | Quinn | project | metrics | code_analysis |
| 2. Security | POST /quality/security | Quinn | code | vulnerabilities | security |
| 3. Review | POST /quality/review | Marcus | all_results | recommendations | code_analysis |
| 4. Report | POST /quality/report | Diana | review | audit_report | - |

**Dashboards**: quality-dashboard.html, security-dashboard.html

---

## Correct Course (Any Workflow)

**Entry Point**: `/api/workflows/correct-course`

| Step | API | Agent | Input | Output |
|------|-----|-------|-------|--------|
| 1. Analyze Impact | POST /correct-course/analyze | SM | change_request | impact_assessment |
| 2. Propose Solution | POST /correct-course/propose | PM/Architect | impact | options[] |
| 3. Update Docs | POST /correct-course/update | PM | decision | updated_artifacts |

---

## Code Review Workflow

**Entry Point**: `/api/workflows/code-review`

| Step | API | Agent | Input | Output |
|------|-----|-------|-------|--------|
| 1. Analyze | POST /code-review/analyze | Quinn | PR/code | issues[] |
| 2. Security | POST /code-review/security | Quinn | code | vulnerabilities |
| 3. Feedback | POST /code-review/feedback | DEV | analysis | review_comments |

**Dashboard**: quality-dashboard.html

---

## Database Tables

| Workflow | Primary Table | Related Tables |
|----------|---------------|----------------|
| MAINTENANCE | technical_debt | code_analysis, items |
| BUG | bug | items, test_results |
| QUALITY_AUDIT | code_analysis | security, quality_gates |
| CODE_REVIEW | code_analysis | items |

---

## Workflow Navigation

### Entry Points
- **From GREEN_PAPER**: After initial development complete
- **From BROWN_PAPER**: For existing system improvements
- **From MIGRATION**: After migration complete
- **Dashboard**: `maintenance-scheduler.html`

### Output → Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Tech Debt Analysis | technical-debt-dashboard.html | → MIGRATION (if major modernization needed) |
| Bug Found | kanban-dashboard.html | → BUG workflow |
| Quality Issues | quality-dashboard.html | → CODE_REVIEW |

### Typical Flow
```
Any Workflow → MAINTENANCE → BUG (loop)
                          → MIGRATION (lifecycle restart)
```

### Lifecycle Restart Trigger
From MAINTENANCE, when analysis reveals:
- Legacy technology constraints
- Major architectural debt
- End-of-life dependencies

→ Trigger MIGRATION workflow for full modernization

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
