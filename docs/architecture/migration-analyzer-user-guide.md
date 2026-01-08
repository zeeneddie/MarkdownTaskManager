# Migration Analyzer User Guide

**Week 70 - MigrationAnalyzer Multi-Agent System**

The Migration Analyzer is a comprehensive tool for analyzing legacy codebases and planning migrations to modern technology stacks. It uses a multi-agent architecture with Miguel as the orchestrator.

---

## Quick Start

### 1. Access the Dashboard

Navigate to: `http://localhost:8000/migration-analyzer.html`

### 2. Create a New Analysis

1. Click the **"New Analysis"** tab
2. Enter the repository path (e.g., `/path/to/legacy-project`)
3. Select the target stack (e.g., `.NET 8`, `React`, `Spring Boot`)
4. Optionally select a target database
5. Click **"Start Analysis"**

### 3. Monitor Progress

- The Overview tab shows all analyses with their status
- Click an analysis to see detailed results
- Auto-refresh updates every 30 seconds

---

## Features

### Stack Detection

The analyzer detects 13+ technology stacks:

| Stack | Description |
|-------|-------------|
| `aspnet_webforms` | Legacy ASP.NET WebForms |
| `asp_classic` | Classic ASP (VBScript/JScript) |
| `angularjs` | AngularJS 1.x |
| `jquery` | jQuery-based applications |
| `php_legacy` | Legacy PHP (< 7.0) |
| `laravel` | Laravel PHP framework |
| `java_legacy` | Java without modern frameworks |
| `spring` | Spring Framework (non-Boot) |
| `struts` | Apache Struts |
| `django` | Django Python framework |
| `flask` | Flask Python framework |
| `ruby_rails` | Ruby on Rails |
| `express` | Express.js (Node.js) |

### Database Analysis

Supports three major database platforms:

| Database | Patterns Detected |
|----------|-------------------|
| **SQL Server** | T-SQL syntax, IDENTITY columns, TOP clause, NVARCHAR |
| **Oracle** | PL/SQL syntax, ROWNUM, DECODE, NVL functions |
| **MySQL** | AUTO_INCREMENT, LIMIT clause, backtick identifiers |

### Data Type Mappings

Automatic type conversion recommendations:

**SQL Server to PostgreSQL:**
- `NVARCHAR` → `VARCHAR` (UTF-8 native)
- `DATETIME` → `TIMESTAMP`
- `BIT` → `BOOLEAN`
- `UNIQUEIDENTIFIER` → `UUID`
- `MONEY` → `NUMERIC(19,4)`

**Oracle to PostgreSQL:**
- `VARCHAR2` → `VARCHAR`
- `NUMBER` → `NUMERIC`
- `DATE` → `TIMESTAMP`
- `CLOB` → `TEXT`
- `BLOB` → `BYTEA`

---

## Analysis Workflow

### Phases

1. **PENDING** - Analysis created, waiting to start
2. **DETECTION** - Source stack detection
3. **STACK_ANALYSIS** - Frontend/backend pattern analysis
4. **DB_ANALYSIS** - Database schema and query analysis
5. **CROSS_CUTTING** - Security, performance, dependency analysis
6. **OUTPUT** - Report generation
7. **COMPLETED** - Analysis finished successfully
8. **FAILED** - Analysis encountered errors

### Agent Assignments

| Agent | Role |
|-------|------|
| **Miguel** | Orchestrator - coordinates all migration tasks |
| **Quinn** | Security analysis - identifies vulnerabilities |
| **Eliza** | Effort estimation - calculates function points |
| **Felix** | Architecture recommendations |
| **Diana** | Report generation |

---

## API Reference

### Endpoints

#### Create Analysis
```http
POST /api/migration/analyze
Content-Type: application/json

{
  "repo_path": "/path/to/repository",
  "target_stack": "dotnet8",
  "target_db": "postgresql"
}
```

#### List Analyses
```http
GET /api/migration/analyses?limit=10&offset=0
```

#### Get Analysis Details
```http
GET /api/migration/analyses/{analysis_id}
```

#### Run Analysis
```http
POST /api/migration/analyses/{analysis_id}/run
```

#### Get Modules
```http
GET /api/migration/analyses/{analysis_id}/modules
```

#### Get Patterns
```http
GET /api/migration/analyses/{analysis_id}/patterns
```

#### Get Recommendations
```http
GET /api/migration/analyses/{analysis_id}/recommendations
```

#### Get Risks
```http
GET /api/migration/analyses/{analysis_id}/risks
```

#### Get Summary
```http
GET /api/migration/analyses/{analysis_id}/summary
```

---

## Response Schemas

### Analysis Object
```json
{
  "id": "uuid",
  "repo_name": "project-name",
  "repo_path": "/path/to/project",
  "target_stack": "dotnet8",
  "target_db": "postgresql",
  "status": "pending|detection|stack_analysis|db_analysis|cross_cutting|output|completed|failed",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:05:00Z"
}
```

### Module Object
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "name": "UserService",
  "type": "backend|frontend|database|integration",
  "source_stack": "aspnet_webforms",
  "complexity": "low|medium|high",
  "file_count": 15,
  "line_count": 2500
}
```

### Pattern Object
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "module_id": "uuid",
  "pattern_type": "code|database|config",
  "name": "Entity Framework",
  "occurrences": 45,
  "migration_impact": "low|medium|high"
}
```

### Recommendation Object
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "category": "architecture|performance|security|testing",
  "priority": "low|medium|high|critical",
  "title": "Migrate to Entity Framework Core",
  "description": "Replace Entity Framework 6 with EF Core for better performance",
  "effort_estimate": "medium",
  "agent_id": "felix"
}
```

### Risk Object
```json
{
  "id": "uuid",
  "analysis_id": "uuid",
  "category": "technical|business|security|compliance",
  "severity": "low|medium|high|critical",
  "title": "Legacy Authentication Mechanism",
  "description": "Forms authentication needs migration to modern identity provider",
  "mitigation": "Implement OpenID Connect with Azure AD B2C",
  "agent_id": "quinn"
}
```

---

## Best Practices

### Before Analysis

1. **Ensure read access** to the target repository
2. **Document known issues** for comparison with findings
3. **Identify critical modules** that need special attention

### During Analysis

1. **Monitor progress** via the dashboard
2. **Check logs** for detailed information
3. **Note any failures** for manual review

### After Analysis

1. **Review all recommendations** before implementing
2. **Prioritize by risk and effort**
3. **Create migration plan** based on module dependencies
4. **Estimate total effort** using function point calculations

---

## Troubleshooting

### Analysis Stuck in Detection Phase

- Verify the repository path is accessible
- Check file permissions
- Review backend logs for errors

### No Patterns Detected

- Ensure the repository contains source code files
- Check that the technology stack is supported
- Try running with a different target stack

### Database Analysis Empty

- Confirm SQL files exist in the repository
- Verify connection strings are not needed for static analysis
- Check for non-standard file extensions

---

## Integration with Other Agents

The Migration Analyzer integrates with the full agent ecosystem:

| Integration | Description |
|-------------|-------------|
| **Quinn Security** | Week 68 - Vulnerability scanning during migration |
| **Eliza Estimation** | Week 68 - Function point calculation for migration effort |
| **Felix Architecture** | Week 68 - Target architecture recommendations |
| **Diana Reports** | Week 68 - Markdown report generation |

---

## Version History

| Version | Week | Changes |
|---------|------|---------|
| 1.0 | 65 | Initial MigrationAnalyzer service |
| 2.0 | 68 | Quinn/Eliza/Felix/Diana integration |
| 3.0 | 70 | Dashboard UI, comprehensive tests (157 tests) |

---

**Related Documentation:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture
- [AGENTS.md](../../AGENTS.md) - Agent reference
- [ROADMAP.md](../../ROADMAP.md) - Development roadmap
