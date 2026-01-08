# Quality-Functionality Impact Mapping

**Fase 29 - Week 148-150**
**Status:** PLANNED
**Priority:** HIGH

---

## Executive Summary

Bij kwaliteitsanalyses (Brown Paper, Migration, Security Scans) worden issues gedetecteerd maar niet gekoppeld aan de **functionaliteit** die erdoor wordt geraakt. Dit document beschrijft de architectuur voor het automatisch mappen van kwaliteitsissues naar Epic/Feature/Story/Task niveau.

### Probleem

```
HUIDIGE STAAT:
├── Security Issue: "Unencrypted data transmission in line 145"
│   └── Geen link naar: Welke functionaliteit? Welke gebruikers geraakt?
│
├── Performance Issue: "Missing index on Patient.BSN query"
│   └── Geen link naar: Welke schermen traag? Welke business flows?
│
├── Memory Leak: "Connection never closed in SaveDeclaratie()"
│   └── Geen link naar: Welke declaratie-flows crashen?
│
└── Code Duplication: "CalculateTarief() in 5 files"
    └── Geen link naar: Welke tarief-features inconsistent?
```

### Gewenste Staat

```
DOEL:
├── Security Issue: "Unencrypted data transmission"
│   ├── Impact: Epic "Declaratieverwerking"
│   ├── Feature: "Vecozo Declaratie Verzending"
│   ├── Story: "Declaratie naar verzekeraar sturen"
│   ├── Users Affected: ~2,500/dag
│   └── Risk: DATA PRIVACY - BSN en medische data
│
├── Performance Issue: "Missing index"
│   ├── Impact: Feature "Patiënt Zoeken"
│   ├── Affected Screens: PatientSearch.asp, PatientList.asp
│   ├── Daily Queries: ~15,000
│   └── Latency Impact: +800ms per query
│
└── Memory Leak: "Connection leak"
    ├── Impact: Epic "Facturatie"
    ├── Feature: "Declaratie Opslaan"
    ├── Crash Probability: 95% bij batch > 100 declaraties
    └── Business Impact: Factuurrun faalt na ~2 uur
```

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    QUALITY-FUNCTIONALITY IMPACT MAPPER                           │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      QualityImpactMappingService                         │    │
│  │                         (Orchestrator)                                   │    │
│  └───────────────────────────────┬──────────────────────────────────────────┘    │
│                                  │                                               │
│     ┌────────────────────────────┼────────────────────────────────────┐         │
│     │                            │                                    │         │
│     ▼                            ▼                                    ▼         │
│  ┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐     │
│  │ CodeToFunc   │     │ FunctionalityDB   │     │ ImpactScoreCalculator  │     │
│  │ Mapper       │     │ (Epic/Feature/    │     │ (Risk x Frequency x     │     │
│  │              │     │  Story Cache)     │     │  Users)                 │     │
│  └──────┬───────┘     └────────┬─────────┘     └───────────┬─────────────┘     │
│         │                      │                           │                    │
│         │    ┌─────────────────┴───────────────────┐      │                    │
│         │    │                                     │      │                    │
│         ▼    ▼                                     ▼      ▼                    │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                        QUALITY ISSUE SOURCES                           │    │
│  ├────────────┬────────────┬────────────┬────────────┬──────────────────┤    │
│  │ Security   │ Performance│ Memory     │ Duplication│ Error Handling   │    │
│  │ Scanner    │ Analyzer   │ Leak       │ Detector   │ Analyzer         │    │
│  │ (GhostCrew)│ (SQL/Index)│ Detector   │            │                  │    │
│  └────────────┴────────────┴────────────┴────────────┴──────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Issue Types & Mapping Strategy

| Issue Type | Detection Source | Mapping Strategy | Impact Metrics |
|------------|------------------|------------------|----------------|
| **Security/Privacy** | GhostCrew, StaticAnalysis | Data flow analysis: waar komt data vandaan, waar gaat het naartoe | Users exposed, data types, compliance risk |
| **Performance** | SQLAnalyzer, IndexAnalyzer | Query → Table → CRUD Operations → Features | Latency, daily queries, affected users |
| **Memory Leaks** | StabilityAnalyzer | Function → Call graph → Entry points → User flows | Crash probability, uptime impact |
| **Code Duplication** | DuplicateDetector | Cluster analysis → Shared functionality → Inconsistency risk | Maintenance cost, bug propagation risk |
| **Error Handling** | ExceptionAnalyzer | Exception types → User-facing errors → UX impact | Error frequency, user frustration |

---

## Detailed Issue Type Specifications

### 1. Security & Data Privacy Issues

**Detection Sources:**
- GhostCrew security scans
- Static analysis (OWASP patterns)
- Data flow analysis

**Impact Mapping:**

```python
class SecurityImpactMapper:
    """Map security issues to affected functionality."""

    PRIVACY_DATA_PATTERNS = {
        "BSN": {"risk": "HIGH", "regulation": "GDPR, AVG"},
        "medical_data": {"risk": "CRITICAL", "regulation": "WGBO"},
        "financial_data": {"risk": "HIGH", "regulation": "PCI-DSS"},
        "personal_email": {"risk": "MEDIUM", "regulation": "GDPR"},
        "ip_address": {"risk": "MEDIUM", "regulation": "GDPR"},
    }

    VULNERABILITY_TYPES = {
        "unencrypted_transmission": {
            "description": "Data verzonden zonder encryptie",
            "impact": "Data kan worden onderschept",
            "severity": "CRITICAL" if data_type in ["BSN", "medical"] else "HIGH",
        },
        "sql_injection": {
            "description": "SQL injection vulnerability",
            "impact": "Database kan worden uitgelezen/gewijzigd",
            "severity": "CRITICAL",
        },
        "xss": {
            "description": "Cross-site scripting vulnerability",
            "impact": "Session hijacking, data theft",
            "severity": "HIGH",
        },
        "hardcoded_credentials": {
            "description": "Wachtwoord in broncode",
            "impact": "Unauthorized access",
            "severity": "CRITICAL",
        },
    }
```

**Example Output:**

```json
{
  "issue_id": "SEC-001",
  "type": "unencrypted_transmission",
  "location": {
    "file": "Declaraties/Vecozo_Send.asp",
    "line": 145,
    "function": "SendDeclaratieToVecozo"
  },
  "data_exposed": ["BSN", "diagnose_code", "behandeling"],
  "impact": {
    "epic": "Declaratieverwerking",
    "feature": "Vecozo Declaratie Verzending",
    "story": "Declaratie naar verzekeraar sturen",
    "affected_users_daily": 2500,
    "regulatory_risk": ["GDPR", "WGBO", "NEN7510"],
    "business_impact": "Mogelijke boete tot 4% omzet, reputatieschade"
  },
  "severity": "CRITICAL",
  "fix_priority": 1
}
```

### 2. Performance Issues

**Detection Sources:**
- SQL Query Analyzer (missing indexes, N+1 queries)
- Database schema analysis
- Query execution plan analysis
- Response time monitoring

**Impact Mapping:**

```python
class PerformanceImpactMapper:
    """Map performance issues to user-facing impact."""

    def analyze_query_impact(self, query_location: str, table: str) -> PerformanceImpact:
        """
        1. Find table in schema
        2. Find all queries using this table
        3. Map queries to functions
        4. Map functions to user-facing screens
        5. Estimate daily query volume
        6. Calculate latency impact
        """

    INDEX_ISSUE_TYPES = {
        "missing_index": {
            "typical_impact_ms": 500-2000,
            "severity_if_daily_queries_gt_1000": "HIGH",
        },
        "wrong_index_order": {
            "typical_impact_ms": 100-500,
            "severity": "MEDIUM",
        },
        "missing_covering_index": {
            "typical_impact_ms": 50-200,
            "severity": "LOW",
        },
        "index_fragmentation": {
            "typical_impact_ms": 100-500,
            "severity": "MEDIUM",
        },
    }
```

**Example Output:**

```json
{
  "issue_id": "PERF-001",
  "type": "missing_index",
  "location": {
    "table": "Patient",
    "column": "BSN",
    "query_file": "PatientSearch.asp",
    "line": 89
  },
  "impact": {
    "feature": "Patiënt Zoeken",
    "affected_screens": ["PatientSearch.asp", "PatientList.asp", "Dashboard.asp"],
    "daily_queries": 15000,
    "avg_latency_current_ms": 1200,
    "avg_latency_with_fix_ms": 45,
    "user_wait_time_saved_daily_hours": 4.8,
    "affected_users": 150
  },
  "severity": "HIGH",
  "fix_complexity": "LOW",
  "recommended_fix": "CREATE INDEX IX_Patient_BSN ON Patient(BSN) INCLUDE (Naam, Geboortedatum)"
}
```

### 3. Memory Leaks & Resource Issues

**Detection Sources:**
- ASP Stability Analyzer (Fase 21)
- ADO Connection Tracker
- COM Object Lifecycle Analyzer

**Impact Mapping:**

```python
class MemoryLeakImpactMapper:
    """Map memory leaks to functionality and crash probability."""

    def calculate_crash_probability(
        self,
        leak_type: str,
        leaks_per_operation: int,
        operations_per_hour: int,
        resource_pool_size: int
    ) -> CrashProbability:
        """
        Calculate when system will crash based on leak rate.

        Example:
        - 1 connection leak per declaratie
        - 100 declaraties/uur in batch
        - Connection pool: 50 connections
        - Time to crash: 30 minutes
        """

    def map_to_functionality(self, leak_location: str) -> FunctionalityImpact:
        """
        1. Find function containing leak
        2. Trace call graph to entry points
        3. Map entry points to user actions
        4. Calculate usage frequency
        5. Determine crash impact
        """
```

**Example Output:**

```json
{
  "issue_id": "LEAK-001",
  "type": "ado_connection_leak",
  "location": {
    "file": "Declaraties/Declaratie_Save.asp",
    "line": 234,
    "function": "SaveDeclaratie",
    "pattern": "LOOP_LEAK"
  },
  "leak_metrics": {
    "leaks_per_operation": 1,
    "operations_in_batch": 500,
    "connection_pool_size": 50
  },
  "impact": {
    "epic": "Facturatie",
    "feature": "Declaratie Opslaan",
    "story": "Batch declaraties verwerken",
    "crash_probability": "95% bij batch > 100",
    "mean_time_to_crash": "32 minuten bij continu gebruik",
    "business_impact": "Nachtelijke factuurrun faalt, €50K/dag omzetverlies"
  },
  "severity": "CRITICAL",
  "fix_priority": 1
}
```

### 4. Code Duplication

**Detection Sources:**
- DuplicateDetector service
- Clone detection algorithms
- Semantic similarity analysis

**Impact Mapping:**

```python
class DuplicationImpactMapper:
    """Map code duplicates to functionality consistency risk."""

    def analyze_duplicate_cluster(
        self,
        duplicate_locations: List[FileLocation],
        similarity_score: float
    ) -> DuplicationImpact:
        """
        1. Identify what functionality is duplicated
        2. Check for differences between copies
        3. Calculate inconsistency risk
        4. Determine maintenance burden
        5. Map to affected features
        """

    RISK_FACTORS = {
        "identical_copies": {
            "maintenance_multiplier": len(copies),
            "bug_propagation_risk": "HIGH if copies > 3",
        },
        "near_duplicates": {
            "inconsistency_risk": "HIGH",
            "behavior_difference_probability": 0.7,
        },
        "business_logic_duplication": {
            "severity": "CRITICAL",
            "reason": "Tarief/prijsberekening kan inconsistent zijn",
        },
    }
```

**Example Output:**

```json
{
  "issue_id": "DUP-001",
  "type": "near_duplicate",
  "locations": [
    {"file": "Tarieven/CalculateTarief.asp", "lines": "45-120"},
    {"file": "Declaraties/BerekenBedrag.asp", "lines": "78-153"},
    {"file": "Facturen/TariefBerekening.asp", "lines": "22-97"},
    {"file": "Offertes/PrijsCalculatie.asp", "lines": "110-185"},
    {"file": "Contracten/TariefHelper.asp", "lines": "200-275"}
  ],
  "similarity_score": 0.87,
  "differences_found": [
    {"type": "value_difference", "description": "BTW percentage: 21% vs 19% vs 9%"},
    {"type": "missing_logic", "description": "Korting niet toegepast in 2 van 5 copies"}
  ],
  "impact": {
    "functionality": "Tariefberekening",
    "affected_features": [
      "Offerte genereren",
      "Declaratie berekenen",
      "Factuur opstellen",
      "Contract prijzen"
    ],
    "inconsistency_risk": "HIGH - Klanten zien verschillende prijzen",
    "maintenance_burden": "5x effort voor elke wijziging",
    "bug_propagation": "Bug fix in 1 file bereikt 4 andere niet"
  },
  "severity": "HIGH",
  "recommended_fix": "Extract naar gedeelde TariefService library"
}
```

### 5. Error Handling Issues

**Detection Sources:**
- Exception Analyzer
- On Error Resume Next pattern detector
- Error logging analysis

**Impact Mapping:**

```python
class ErrorHandlingImpactMapper:
    """Map error handling issues to user experience impact."""

    ERROR_PATTERNS = {
        "silent_failure": {
            "description": "On Error Resume Next zonder logging",
            "user_impact": "Geen feedback, data mogelijk corrupt",
            "severity": "HIGH",
        },
        "generic_error": {
            "description": "Generic 'Er is een fout opgetreden' bericht",
            "user_impact": "Geen actie mogelijk, helpdek nodig",
            "severity": "MEDIUM",
        },
        "exposed_stack_trace": {
            "description": "Technische details zichtbaar voor gebruiker",
            "user_impact": "Verwarrend, security risk",
            "severity": "MEDIUM",
        },
        "no_retry_logic": {
            "description": "Transient failures niet afgevangen",
            "user_impact": "Sporadische fouten bij externe services",
            "severity": "MEDIUM",
        },
    }
```

**Example Output:**

```json
{
  "issue_id": "ERR-001",
  "type": "silent_failure",
  "location": {
    "file": "Declaraties/Vecozo_Response.asp",
    "line": 89,
    "pattern": "On Error Resume Next"
  },
  "error_context": {
    "scope_lines": 45,
    "operations_at_risk": ["XML parsing", "Database insert", "Email send"]
  },
  "impact": {
    "feature": "Vecozo Response Verwerking",
    "story": "Declaratie status updaten",
    "failure_scenarios": [
      "XML parsing faalt → Status blijft 'Verzonden' terwijl afgewezen",
      "Database insert faalt → Declaratie kwijt",
      "Email faalt → Geen notificatie bij afwijzing"
    ],
    "user_impact": "Geen foutmelding, foute status, gemiste deadlines",
    "daily_affected_operations": 800,
    "estimated_silent_failures_daily": 12
  },
  "severity": "HIGH",
  "recommended_fix": "Implement explicit error handling met logging en user feedback"
}
```

---

## Database Schema

```sql
-- Quality Issue to Functionality mapping
CREATE TABLE quality_functionality_mappings (
    id SERIAL PRIMARY KEY,

    -- Source issue
    issue_id VARCHAR(50) NOT NULL,
    issue_type VARCHAR(50) NOT NULL,  -- security, performance, memory_leak, duplication, error_handling
    issue_source VARCHAR(100),         -- ghostcrew, stability_analyzer, sql_analyzer, etc.

    -- Code location
    file_path TEXT NOT NULL,
    line_number INTEGER,
    function_name VARCHAR(255),

    -- Functionality mapping
    epic_id INTEGER REFERENCES epics(id),
    feature_id INTEGER REFERENCES features(id),
    story_id INTEGER REFERENCES stories(id),
    task_id INTEGER REFERENCES tasks(id),

    -- Impact metrics
    severity VARCHAR(20) NOT NULL,     -- CRITICAL, HIGH, MEDIUM, LOW
    users_affected_daily INTEGER,
    business_impact TEXT,
    fix_priority INTEGER,
    fix_complexity VARCHAR(20),        -- LOW, MEDIUM, HIGH, VERY_HIGH

    -- Specific metrics (JSONB for flexibility)
    impact_details JSONB,              -- Type-specific metrics

    -- Tracking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id)
);

-- Indexes for common queries
CREATE INDEX ix_qfm_issue_type ON quality_functionality_mappings(issue_type);
CREATE INDEX ix_qfm_severity ON quality_functionality_mappings(severity);
CREATE INDEX ix_qfm_epic ON quality_functionality_mappings(epic_id);
CREATE INDEX ix_qfm_feature ON quality_functionality_mappings(feature_id);
CREATE INDEX ix_qfm_file ON quality_functionality_mappings(file_path);

-- Aggregated view per functionality
CREATE VIEW functionality_quality_summary AS
SELECT
    COALESCE(e.title, 'No Epic') as epic,
    COALESCE(f.title, 'No Feature') as feature,
    COUNT(*) as total_issues,
    COUNT(*) FILTER (WHERE qfm.severity = 'CRITICAL') as critical_issues,
    COUNT(*) FILTER (WHERE qfm.severity = 'HIGH') as high_issues,
    COUNT(*) FILTER (WHERE qfm.issue_type = 'security') as security_issues,
    COUNT(*) FILTER (WHERE qfm.issue_type = 'performance') as performance_issues,
    COUNT(*) FILTER (WHERE qfm.issue_type = 'memory_leak') as memory_leak_issues,
    COUNT(*) FILTER (WHERE qfm.issue_type = 'duplication') as duplication_issues,
    COUNT(*) FILTER (WHERE qfm.issue_type = 'error_handling') as error_handling_issues,
    SUM(qfm.users_affected_daily) as total_users_affected
FROM quality_functionality_mappings qfm
LEFT JOIN epics e ON qfm.epic_id = e.id
LEFT JOIN features f ON qfm.feature_id = f.id
WHERE qfm.resolved_at IS NULL
GROUP BY e.title, f.title
ORDER BY critical_issues DESC, high_issues DESC;
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quality-impact/analyze` | POST | Run quality-to-functionality mapping |
| `/api/quality-impact/project/{id}` | GET | Get all mappings for project |
| `/api/quality-impact/epic/{id}` | GET | Get issues affecting epic |
| `/api/quality-impact/feature/{id}` | GET | Get issues affecting feature |
| `/api/quality-impact/by-type/{type}` | GET | Get issues by type (security, performance, etc.) |
| `/api/quality-impact/summary/{project_id}` | GET | Aggregated summary per functionality |
| `/api/quality-impact/critical/{project_id}` | GET | Critical issues with business impact |
| `/api/quality-impact/fix-plan/{project_id}` | GET | Prioritized fix plan |

---

## Dashboard Design

### Functionality Quality Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FUNCTIONALITY QUALITY DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EPIC: Declaratieverwerking                          HEALTH: ⚠️ 45%  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                     │    │
│  │  🔴 CRITICAL ISSUES (3)                                            │    │
│  │  ├── SEC-001: Unencrypted BSN transmission (Vecozo Send)           │    │
│  │  ├── LEAK-001: Connection leak in batch processing                 │    │
│  │  └── ERR-001: Silent failure in response handling                  │    │
│  │                                                                     │    │
│  │  🟠 HIGH ISSUES (5)                                                │    │
│  │  ├── PERF-002: Missing index on DeclaratieStatus                   │    │
│  │  ├── DUP-001: Tarief calculation duplicated 5x                     │    │
│  │  └── ... +3 more                                                   │    │
│  │                                                                     │    │
│  │  FEATURES AFFECTED:                                                │    │
│  │  ├── Vecozo Declaratie Verzending    [🔴🔴🟠]                      │    │
│  │  ├── Batch Declaratie Verwerking     [🔴🟠🟠🟠]                    │    │
│  │  └── Declaratie Status Tracking      [🟠🟡]                        │    │
│  │                                                                     │    │
│  │  IMPACT: 2,500 users/day | €50K/day risk | NEN7510 compliance ⚠️   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EPIC: Patiëntbeheer                                  HEALTH: ✅ 78%  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  🟠 HIGH (2) | 🟡 MEDIUM (4) | ⚪ LOW (8)                           │    │
│  │  Main issue: Performance - Patient search slow during peak hours   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Issue Type Distribution per Functionality

```
┌────────────────────────────────────────────────────────────────┐
│  ISSUE TYPES BY EPIC                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Declaratieverwerking  ████████████████████████████  (28)     │
│                        🔴 Security: 8                          │
│                        ⚡ Performance: 5                        │
│                        💾 Memory Leaks: 6                       │
│                        📋 Duplication: 4                        │
│                        ⚠️ Error Handling: 5                     │
│                                                                │
│  Patiëntbeheer         ██████████████  (14)                   │
│                        ⚡ Performance: 8                        │
│                        📋 Duplication: 4                        │
│                        ⚠️ Error Handling: 2                     │
│                                                                │
│  Agenda                ████████  (8)                          │
│                        💾 Memory Leaks: 5                       │
│                        ⚡ Performance: 3                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

| System | Integration | Data Flow |
|--------|-------------|-----------|
| **GhostCrew** | Security issue source | GhostCrew findings → Impact Mapper |
| **StabilityAnalyzer** | Memory leak source | Leak findings → Impact Mapper |
| **CodeAnalysisAggregator** | Duplication source | Clone clusters → Impact Mapper |
| **SQLAnalyzer** | Performance source | Query issues → Impact Mapper |
| **HierarchicalExtraction** | Functionality mapping | Code → Epic/Feature/Story |
| **Brown Paper** | Trigger analysis | On analysis complete → Run mapping |
| **Quality Gates** | Block on impact | Check critical impacts before deploy |
| **Technical Debt** | Auto-create items | High impact issues → Debt items |

---

## Week-by-Week Implementation Plan

### Week 148: Core Framework & Security Mapping

| Task | Hours | Output |
|------|-------|--------|
| `QualityImpactMappingService` base | 6 | Orchestrator |
| `CodeToFunctionalityMapper` | 8 | File → Epic/Feature/Story |
| `SecurityImpactMapper` | 8 | Security issues → functionality |
| Database migration | 2 | Tables & indexes |
| Unit tests | 6 | 40+ tests |
| **Total** | **30** | |

### Week 149: Performance & Memory Leak Mapping

| Task | Hours | Output |
|------|-------|--------|
| `PerformanceImpactMapper` | 8 | Query issues → functionality |
| `MemoryLeakImpactMapper` | 8 | Leaks → crash probability |
| `ImpactScoreCalculator` | 4 | Risk × Frequency × Users |
| Integration with StabilityAnalyzer | 4 | Leak data flow |
| Unit tests | 6 | 40+ tests |
| **Total** | **30** | |

### Week 150: Duplication, Errors & Dashboard

| Task | Hours | Output |
|------|-------|--------|
| `DuplicationImpactMapper` | 6 | Clones → inconsistency risk |
| `ErrorHandlingImpactMapper` | 6 | Error patterns → UX impact |
| API endpoints (8) | 6 | REST API |
| Quality Impact Dashboard | 8 | `quality-impact-dashboard.html` |
| Brown Paper integration | 2 | Auto-run after analysis |
| Documentation | 2 | User guide |
| **Total** | **30** | |

### Total Effort: 90 hours (3 weeks)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Issue mapping accuracy | >85% correctly linked to functionality |
| Functionality coverage | 95% of issues mapped to Epic/Feature |
| User impact calculation | >80% accuracy on affected users |
| Dashboard usability | <30 sec to understand quality per feature |
| Integration completeness | All 5 issue sources connected |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 21 (Stability Analyzer) | PLANNED | Memory leak source |
| GhostCrew | COMPLETE | Security issue source |
| HierarchicalStoryExtraction | EXISTS | Code → functionality mapping |
| CodeAnalysisAggregator | EXISTS | Duplication detection |
| Brown Paper Enhanced | PLANNED | Integration point |

---

## References

| Source | Usage |
|--------|-------|
| [Stability Analyzer Spec](asp-stability-analyzer-framework.md) | Memory leak detection |
| [GhostCrew Security](ghostcrew-security.md) | Security issue source |
| [Brown Paper Enhanced](brown-paper-enhanced.md) | Integration target |
| [Deep Extraction](deep-extraction-pipeline.md) | Hierarchical functionality mapping |
