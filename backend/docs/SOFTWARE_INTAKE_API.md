# Software Intake API - Frontend Data Contract

**Version:** 1.0.0
**Last Updated:** Week 158 (January 2026)
**Base URL:** `/api/software-intake`

## Overview

The Software Intake API provides automated, code-driven analysis of source code projects without requiring user questions. It scans source code, detects technologies, analyzes security issues, and estimates migration effort.

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Start intake analysis |
| GET | `/{intake_id}/progress` | Get analysis progress |
| GET | `/{intake_id}/progress/stream` | SSE real-time progress |
| GET | `/{intake_id}` | Get complete report |
| GET | `/` | List all intakes |
| DELETE | `/{intake_id}` | Delete intake |
| GET | `/{intake_id}/export` | Export report |
| POST | `/{intake_id}/rerun` | Re-run analysis |

---

## 1. Start Analysis

**POST** `/api/software-intake/analyze`

### Request Body

```json
{
  "project_path": "/path/to/source/code",
  "project_name": "My Project",        // Optional
  "target_stack": "dotnet8",           // Optional: dotnet8, python_fastapi, nodejs_nestjs, java_spring
  "include_phases": ["security", "estimation"]  // Optional: limit phases
}
```

### Response

```json
{
  "intake_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "analyzing",
  "message": "Intake analysis started",
  "progress_url": "/api/software-intake/123e4567-e89b-12d3-a456-426614174000/progress"
}
```

---

## 2. Get Progress

**GET** `/api/software-intake/{intake_id}/progress`

### Response

```json
{
  "intake_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "analyzing",              // pending, analyzing, completed, failed
  "current_phase": "security",
  "progress_percent": 45,
  "phases_completed": ["stack_detection", "code_metrics"],
  "phases_pending": ["estimation", "architecture", "dependencies", "business_rules", "aggregation"],
  "error_message": null
}
```

### Analysis Phases (in order)

1. `stack_detection` (5%) - Detect languages, frameworks, databases
2. `code_metrics` (20%) - LOC, complexity, duplication
3. `security` (20%) - CWE issues, OWASP coverage
4. `estimation` (15%) - Function points, effort hours
5. `architecture` (15%) - Layer detection, component mapping
6. `dependencies` (10%) - Internal/external dependency graph
7. `business_rules` (10%) - Extract embedded business logic
8. `aggregation` (5%) - Compile findings and recommendations

---

## 3. Get Complete Report

**GET** `/api/software-intake/{intake_id}`

### Response: IntakeReport

```json
{
  "id": "uuid",
  "project_path": "/path/to/project",
  "project_name": "My Project",
  "analyzed_at": "2026-01-20T10:30:00Z",
  "analysis_duration_seconds": 45.5,
  "status": "completed",
  "progress_percent": 100,
  "error_message": null,

  "summary": {
    "total_files": 350,
    "total_loc": 189000,
    "total_blank_lines": 25000,
    "total_comment_lines": 15000,
    "languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI", "React"],
    "databases": ["PostgreSQL", "Redis"],
    "primary_language": "Python",
    "primary_framework": "FastAPI",
    "health_score": 75,                    // 0-100
    "migration_complexity": "medium",       // low, medium, high, critical
    "security_issues_count": 12,
    "quality_issues_count": 45,
    "deprecated_dependencies_count": 8
  },

  "findings": {
    "summary": {
      "total": 65,
      "critical": 2,
      "high": 10,
      "medium": 35,
      "low": 15,
      "info": 3
    },
    "by_category": {
      "security": {
        "count": 12,
        "items": [/* Finding objects */]
      },
      "quality": { /* ... */ },
      "architecture": { /* ... */ },
      "performance": { /* ... */ },
      "maintainability": { /* ... */ }
    },
    "top_10_priority": [/* Top 10 Finding objects */],
    "roadmap": [/* FindingRoadmapItem objects */],
    "health_score": 75
  },

  "code_metrics": {
    "total_files": 350,
    "total_loc": 189000,
    "by_language": {
      "Python": {
        "file_count": 200,
        "loc": 150000,
        "blank_lines": 20000,
        "comment_lines": 12000
      }
    },
    "complexity": {
      "average_complexity": 8.5,
      "max_complexity": 45,
      "files_above_threshold": 15
    },
    "duplication": {
      "duplication_percent": 5.5,
      "duplicate_blocks": 23
    }
  },

  "security": {
    "risk_score": 35.5,
    "findings_by_severity": {
      "critical": 2,
      "high": 5,
      "medium": 5
    },
    "owasp_coverage": [
      {
        "category": "A01:2021-Broken Access Control",
        "findings_count": 3,
        "risk_level": "high"
      }
    ],
    "cwe_coverage": [
      {
        "cwe_id": "CWE-79",
        "cwe_name": "Cross-site Scripting (XSS)",
        "findings_count": 2
      }
    ],
    "top_findings": [/* Finding objects */],
    "migration_blockers": [/* Finding objects */],
    "estimated_remediation_hours": 40.0,
    "scanners_used": ["semgrep", "bandit"]
  },

  "estimation": {
    "function_points_raw": 1500,
    "function_points_adjusted": 1650,
    "effort_hours": 8250,
    "effort_months": 51.5,
    "confidence": "medium",              // low, medium, high
    "effort_distribution": {
      "development": 4125,
      "testing": 2062,
      "documentation": 825,
      "deployment": 825,
      "project_management": 413
    },
    "phases": [
      {
        "phase": "discovery",
        "description": "Requirements gathering and analysis",
        "activities": ["Stakeholder interviews", "Document review"],
        "base_hours": 200,
        "risk_buffer_hours": 40,
        "total_hours": 240,
        "percentage_of_total": 3
      }
    ],
    "assumptions": ["Full team availability", "No major scope changes"],
    "risks": ["Legacy system complexity", "Data migration challenges"]
  },

  "architecture": {
    "recommended_pattern": "modular_monolith",  // layered, clean, microservices, etc.
    "recommended_strategy": "incremental",       // big_bang, incremental, strangler
    "detected_layers": [
      {
        "name": "presentation",
        "description": "Contains 15 components",
        "file_count": 15,
        "loc": 5000
      }
    ],
    "component_mapping": [
      {
        "legacy_component": "UserController",
        "legacy_type": "controller",
        "legacy_location": "/src/controllers/UserController.cs",
        "target_component": "UserService",
        "target_type": "service",
        "migration_strategy": "refactor",
        "effort_hours": 16
      }
    ],
    "architecture_issues": [/* Finding objects */]
  },

  "dependencies": {
    "total_dependencies": 45,
    "internal_dependencies": [
      {
        "source_module": "services",
        "target_module": "repositories",
        "dependency_type": "import"
      }
    ],
    "external_dependencies": [
      {
        "name": "fastapi",
        "version": "0.109.0",
        "latest_version": "0.115.0",
        "is_outdated": true,
        "has_vulnerabilities": false,
        "license": "MIT"
      }
    ],
    "outdated_count": 8,
    "vulnerable_count": 1,
    "circular_dependencies": []
  },

  "business_rules": {
    "total_rules_extracted": 25,
    "rules": [
      {
        "id": "BR-001",
        "description": "User must be verified before placing orders",
        "source_file": "/src/services/OrderService.py",
        "source_line": 45,
        "category": "validation",
        "complexity": "medium",
        "dependencies": ["UserService", "OrderRepository"]
      }
    ],
    "coverage_by_category": {
      "validation": 10,
      "calculation": 8,
      "workflow": 5,
      "integration": 2
    }
  },

  "technical_debt": {
    "total_debt_hours": 500,
    "debt_ratio": 12.5,
    "by_type": {
      "code_duplication": 100,
      "complexity": 150,
      "outdated_dependencies": 80,
      "missing_tests": 120,
      "documentation": 50
    },
    "top_debt_items": [/* TechnicalDebtItem objects */]
  },

  "quick_wins": [
    {
      "id": "QW-001",
      "title": "Update deprecated dependencies",
      "description": "8 packages are outdated and can be updated with minimal effort",
      "category": "dependencies",
      "effort_hours": 4,
      "impact": "high",
      "priority": 1
    }
  ],

  "recommendations": [
    {
      "id": "REC-001",
      "title": "Implement API versioning",
      "description": "Add API versioning to ensure backward compatibility",
      "category": "architecture",
      "priority": "high",
      "effort": "medium",
      "benefit": "Enables incremental migration without breaking clients"
    }
  ],

  "scanners_used": [
    "stack_detection",
    "code_metrics",
    "security_scan",
    "estimation",
    "architecture",
    "dependencies",
    "business_rules"
  ],

  "analysis_options": {
    "target_stack": "dotnet8",
    "include_phases": null,
    "skip_phases": null
  }
}
```

---

## 4. List All Intakes

**GET** `/api/software-intake`

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (pending, analyzing, completed, failed) |
| limit | int | Max results (default: 20, max: 100) |
| offset | int | Pagination offset |

### Response

```json
{
  "intakes": [
    {
      "intake_id": "uuid",
      "project_path": "/path/to/project",
      "project_name": "My Project",
      "status": "completed",
      "health_score": 75,
      "total_files": 350,
      "total_loc": 189000,
      "primary_language": "Python",
      "migration_complexity": "medium",
      "analyzed_at": "2026-01-20T10:30:00Z"
    }
  ],
  "total": 15
}
```

---

## 5. Export Report

**GET** `/api/software-intake/{intake_id}/export`

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | Export format: `json` (default), `markdown` |

### Response

- **JSON**: Returns the full IntakeReport object
- **Markdown**: Returns a formatted markdown document

---

## 6. Delete Intake

**DELETE** `/api/software-intake/{intake_id}`

### Response

```json
{
  "message": "Intake 123e4567-e89b-12d3-a456-426614174000 deleted"
}
```

---

## 7. Re-run Analysis

**POST** `/api/software-intake/{intake_id}/rerun`

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| target_stack | string | Override target stack for re-analysis |

### Response

Returns a new `IntakeAnalyzeResponse` with a new `intake_id`.

---

## 8. Real-time Progress (SSE)

**GET** `/api/software-intake/{intake_id}/progress/stream`

### Event Stream Format

```
data: {"intake_id": "uuid", "status": "analyzing", "current_phase": "security", "progress_percent": 45}

data: {"intake_id": "uuid", "status": "analyzing", "current_phase": "estimation", "progress_percent": 60}

data: {"status": "completed", "done": true}
```

### JavaScript Example

```javascript
const eventSource = new EventSource('/api/software-intake/123/progress/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.done) {
    eventSource.close();
    loadFullReport(data.intake_id);
  } else {
    updateProgressBar(data.progress_percent);
    updateCurrentPhase(data.current_phase);
  }
};

eventSource.onerror = () => {
  console.error('Connection lost');
  eventSource.close();
};
```

---

## Data Types Reference

### Finding

```json
{
  "id": "SEC-001",
  "severity": "high",           // critical, high, medium, low, info
  "category": "security",       // security, quality, architecture, performance, maintainability
  "title": "SQL Injection Risk",
  "description": "Raw SQL query with user input detected",
  "file_path": "/src/db/queries.py",
  "line_number": 45,
  "code_snippet": "SELECT * FROM users WHERE id = {user_id}",
  "recommendation": "Use parameterized queries",
  "effort_hours": 2,
  "cwe_id": "CWE-89",
  "owasp_category": "A03:2021-Injection",
  "tags": ["database", "input-validation"]
}
```

### Complexity Enum Values

- `low`: Simple project, straightforward migration
- `medium`: Moderate complexity, standard patterns
- `high`: Complex architecture, significant effort required
- `critical`: Major challenges, requires careful planning

### Status Enum Values

- `pending`: Analysis queued but not started
- `analyzing`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered an error

---

## Error Responses

### 404 Not Found

```json
{
  "detail": "Intake report {intake_id} not found"
}
```

### 202 Accepted (Analysis Still Running)

```json
{
  "detail": "Analysis still in progress"
}
```
(Headers include `Retry-After: 5`)

### 400 Bad Request

```json
{
  "detail": "Unsupported export format: pdf. Use json or markdown."
}
```

---

## Frontend Integration Example

### Starting Analysis with Progress Updates

```html
<div id="analysis-container">
  <button onclick="startAnalysis()">Start Analysis</button>
  <div id="progress-bar" style="display: none;">
    <div id="progress-fill"></div>
    <span id="progress-text">0%</span>
  </div>
  <div id="current-phase"></div>
  <div id="report-container" style="display: none;"></div>
</div>

<script>
async function startAnalysis() {
  const response = await fetch('/api/software-intake/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_path: '/path/to/project',
      project_name: 'My Project'
    })
  });

  const { intake_id } = await response.json();

  // Show progress bar
  document.getElementById('progress-bar').style.display = 'block';

  // Connect to SSE stream
  const eventSource = new EventSource(`/api/software-intake/${intake_id}/progress/stream`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.done) {
      eventSource.close();
      loadReport(intake_id);
    } else {
      document.getElementById('progress-fill').style.width = `${data.progress_percent}%`;
      document.getElementById('progress-text').textContent = `${data.progress_percent}%`;
      document.getElementById('current-phase').textContent = `Phase: ${data.current_phase}`;
    }
  };
}

async function loadReport(intakeId) {
  const response = await fetch(`/api/software-intake/${intakeId}`);
  const report = await response.json();

  // Hide progress, show report
  document.getElementById('progress-bar').style.display = 'none';
  document.getElementById('report-container').style.display = 'block';

  // Render report sections
  renderSummary(report.summary);
  renderFindings(report.findings);
  renderSecurity(report.security);
  // ... etc
}
</script>
```

---

## Dashboard Cards Layout

Recommended layout for the intake report dashboard:

```
+------------------+------------------+------------------+
|    Summary       |    Health        |    Complexity    |
|    Card          |    Score         |    Indicator     |
+------------------+------------------+------------------+
|                                                        |
|                  Findings Overview                     |
|    [Critical: 2] [High: 10] [Medium: 35] [Low: 15]    |
|                                                        |
+------------------+------------------+------------------+
|    Code          |    Security      |    Estimation    |
|    Metrics       |    Report        |    Summary       |
+------------------+------------------+------------------+
|    Architecture  |    Dependencies  |    Quick Wins    |
|    Report        |    Graph         |    List          |
+------------------+------------------+------------------+
|                                                        |
|              Recommendations Section                   |
|                                                        |
+--------------------------------------------------------+
```

Each section maps to a key in the IntakeReport JSON response.
