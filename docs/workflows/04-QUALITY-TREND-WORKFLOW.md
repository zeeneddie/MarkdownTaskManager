# Quality Trend Workflow (Periodic Quality Monitoring)

> **STATUS: IN PROGRESS** - Domain separation maakt Quality onafhankelijk uitvoerbaar.

## Overview

De Quality Trend workflow meet periodiek de softwarekwaliteit volgens **SIG TOP 10** guidelines en toont trends over tijd in het quality-dashboard. Hergebruikt componenten van QUALITY_AUDIT workflow.

**Use Case**: Continu monitoren van kwaliteitsontwikkeling
**API Prefix**: `/api/quality-trend` (v1), `/api/v2/quality` (v2)
**Primary Agents**: Quinn (Quality Analyst), Marcus (Maintenance)
**Metrics Framework**: SIG/TUViT Maintainability Model

---

## Domain Architecture (v2)

**Specification:** [workflow-separation-plan.md](../architecture/workflow-separation-plan.md)

Quality is the **Validation Domain** - 100% independent. Can run standalone, integrated, or scheduled.

```
+-------------------------------------------------------------------+
|                    QUALITY FLOW (3 MODI)                           |
+-------------------------------------------------------------------+
|                                                                    |
|  MODE 1: Standalone                                                |
|  POST /api/v2/quality/scans/run                                   |
|  -> Direct scan on any project_path                               |
|                                                                    |
|  MODE 2: Integrated in Brown Paper                                 |
|  -> Automatic during Phase 1 analysis                             |
|  -> Results in AnalysisContract.stability                         |
|                                                                    |
|  MODE 3: Scheduled/Audit                                           |
|  POST /api/v2/quality/schedules                                   |
|  -> Daily/Weekly/Interval execution                               |
|  -> Audit trail in quality_scan_results                           |
|                                                                    |
+-------------------------------------------------------------------+
```

### New v2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/quality/scans/run` | POST | Run immediate quality scan |
| `/api/v2/quality/schedules` | POST | Create scheduled scan |
| `/api/v2/quality/schedules` | GET | List scheduled scans |
| `/api/v2/quality/schedules/{id}` | DELETE | Remove schedule |
| `/api/v2/quality/gates/{project_id}` | GET | Evaluate quality gate |

### Scheduling Options

```python
QualitySchedulerService:
    schedule_daily_scan(project_id, hour=2)      # 2:00 AM
    schedule_weekly_scan(project_id, day='mon')  # Monday
    schedule_interval_scan(project_id, hours=24) # Every 24h
    run_immediate_scan(project_id, project_path) # On-demand
```

---

## SIG TOP 10 Quality Metrics

Gebaseerd op het Software Improvement Group (SIG) kwaliteitsmodel:

| # | SIG Metric | Wat het meet | Minimum | Daily | Weekly | Monthly+ |
|---|------------|--------------|:-------:|:-----:|:------:|:--------:|
| 1 | **Volume** | Totale codebase grootte (LOC) | ✓ | - | ✓ | ✓ |
| 2 | **Duplication** | % gedupliceerde code | ✓ | - | ✓ | ✓ |
| 3 | **Unit Size** | Grootte methods/functions (LOC) | - | - | ✓ | ✓ |
| 4 | **Unit Complexity** | Cyclomatic complexity per unit | ✓ | - | ✓ | ✓ |
| 5 | **Unit Interfacing** | Parameters per unit | - | - | - | ✓ |
| 6 | **Module Coupling** | Dependencies tussen modules | - | - | ✓ | ✓ |
| 7 | **Component Balance** | Code verdeling over componenten | - | - | - | ✓ |
| 8 | **Component Independence** | Coupling tussen componenten | - | - | - | ✓ |
| 9 | **Code Comments** | Documentatie ratio | ✓ | - | ✓ | ✓ |
| 10 | **Test Coverage** | Automatische test dekking % | ✓ | ✓ | ✓ | ✓ |
| +1 | **Security** | Vulnerabilities (critical/high/med/low) | ✓ | ✓ | ✓ | ✓ |

### Minimum Baseline (Verplicht voor alle applicaties)

Deze 6 metrics zijn **altijd** actief, ongeacht klantconfiguratie:

| Metric | Waarom verplicht | Threshold |
|--------|------------------|-----------|
| **Volume** | Context over codebase grootte | Tracking only (geen threshold) |
| **Duplication** | Basis voor codekwaliteit | <= 5% |
| **Unit Complexity** | Basis voor onderhoudbaarheid | Avg <= 10, Max <= 25 |
| **Code Comments** | Direct inzicht in documentatie | >= 10% ratio |
| **Test Coverage** | Basis voor betrouwbaarheid | >= 70% |
| **Security Vulnerabilities** | Kritiek voor productie | 0 critical, <= 3 high |

---

## Per-Applicatie Metric Configuratie

### Onboarding Flow
Bij onboarding van een nieuwe applicatie:
1. **Eerste meting**: Meet ALLE SIG TOP 10 + Security
2. **Baseline rapport**: Genereer volledig kwaliteitsrapport
3. **Klantoverleg**: Bespreek resultaten, bepaal focus metrics
4. **Configuratie**: Stel actieve metrics in per applicatie

### Application Metric Configuration

```sql
CREATE TABLE application_quality_config (
    id UUID PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES application_registry(id),

    -- Metric toggles (minimum baseline = 6 metrics, altijd TRUE)
    metric_volume BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true (context)
    metric_duplication BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true
    metric_unit_size BOOLEAN DEFAULT TRUE,
    metric_unit_complexity BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true
    metric_unit_interfacing BOOLEAN DEFAULT FALSE,
    metric_module_coupling BOOLEAN DEFAULT TRUE,
    metric_component_balance BOOLEAN DEFAULT FALSE,
    metric_component_independence BOOLEAN DEFAULT FALSE,
    metric_code_comments BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true (inzicht)
    metric_test_coverage BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true
    metric_security BOOLEAN DEFAULT TRUE,  -- MINIMUM: always true

    -- Custom thresholds (NULL = use defaults)
    threshold_coverage_min DECIMAL,
    threshold_complexity_avg_max DECIMAL,
    threshold_complexity_max DECIMAL,
    threshold_duplication_max DECIMAL,
    threshold_security_critical_max INTEGER,
    threshold_security_high_max INTEGER,

    -- Intervals enabled
    interval_daily BOOLEAN DEFAULT FALSE,
    interval_weekly BOOLEAN DEFAULT TRUE,
    interval_monthly BOOLEAN DEFAULT TRUE,
    interval_quarterly BOOLEAN DEFAULT TRUE,

    -- Audit
    configured_by VARCHAR(100),
    configured_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### API: Configure Application Metrics

```bash
POST /api/quality-trend/config/{application_id}
{
    "metrics": {
        "volume": true,
        "duplication": true,
        "unit_size": true,
        "unit_complexity": true,
        "unit_interfacing": false,
        "module_coupling": true,
        "component_balance": false,
        "component_independence": false,
        "code_comments": false,
        "test_coverage": true,
        "security": true
    },
    "thresholds": {
        "coverage_min": 80,
        "complexity_avg_max": 8
    },
    "intervals": {
        "daily": false,
        "weekly": true,
        "monthly": true,
        "quarterly": true
    }
}
```

---

## Measurement Intervals

| Interval | Frequency | Metrics | Use Case |
|----------|-----------|---------|----------|
| **Daily** | Elke dag 02:00 | Minimum baseline only | Snelle health check |
| **Weekly** | Zondag 03:00 | Configured metrics | Wekelijkse review |
| **Monthly** | 1e van maand | All configured + deep analysis | Maandrapportage |
| **Quarterly** | 1e jan/apr/jul/okt | Full SIG + comparison report | Kwartaalreview |
| **Half-yearly** | 1 jan/jul | Full + extended trend analysis | Halfjaarlijkse audit |
| **Yearly** | 1 januari | Complete audit + recommendations | Jaarlijkse planning |

---

## Trend Comparison

### Vergelijkingsmethode: Rolling Comparison

Elke meting wordt vergeleken met de **vorige meting van hetzelfde interval type**:

| Huidige Meting | Vergelijk Met |
|----------------|---------------|
| Week 5 | Week 4 |
| Januari | December |
| Q1 2026 | Q4 2025 |

```
Week 4        Week 5         Delta
Coverage: 75% → Coverage: 78% → +3% (improving)
Complexity: 8 → Complexity: 9  → +12.5% (degrading)
```

**Trend Direction Values**:
- `improving`: >= +5% verbetering (of afname bij negatieve metrics)
- `stable`: binnen -5% tot +5%
- `degrading`: >= -5% verslechtering
- `critical`: >= -20% of threshold overschreden

---

## Complete Workflow Steps

### Step 1: Schedule Trigger
**Cron-based trigger starts measurement**

| Aspect | Details |
|--------|---------|
| **Trigger** | Cron schedule or manual API call |
| **Service** | `QualityTrendService.trigger_measurement()` |
| **Agent** | None (system) |
| **Input** | `interval_type`, `application_id` |
| **Processing** | Load app config, validate schedule, create job |
| **Output** | `measurement_id`, `status: scheduled` |
| **DB Table** | `quality_measurements` |

---

### Step 2: Metric Collection
**Quinn agent collects quality metrics (hergebruikt QUALITY_AUDIT)**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/quality-trend/{measurement_id}/collect` |
| **Service** | `QualityTrendService.collect_metrics()` |
| **Agent** | **Quinn** (Quality Analyst) |
| **LLM Model** | `codellama:7b` |
| **Input** | `project_path`, `interval_type`, `app_config` |
| **Processing** | Run configured SIG metrics via QUALITY_AUDIT components |
| **Output** | `metrics_snapshot`, `raw_data` |
| **DB Table** | `quality_snapshots` |

**Hergebruik van QUALITY_AUDIT**:
- `QualityAuditService.run_static_analysis()` - SIG metrics 1-9
- `QualityAuditService.run_test_coverage()` - SIG metric 10
- `QualityAuditService.run_security_scan()` - Security metric
- Indien QUALITY_AUDIT deze niet heeft: **uitbreiden**

---

### Step 3: Trend Analysis
**Compare with previous measurement**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/quality-trend/{measurement_id}/analyze` |
| **Service** | `QualityTrendService.analyze_trends()` |
| **Agent** | **Quinn** (Quality Analyst) |
| **LLM Model** | `codellama:7b` |
| **Input** | Current snapshot, previous snapshot (same interval) |
| **Processing** | Delta calculation, trend detection |
| **Output** | `trend_direction`, `delta_metrics`, `anomalies[]` |
| **DB Table** | `quality_trends` |

---

### Step 4: Report Generation
**Generate trend report**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/quality-trend/{measurement_id}/report` |
| **Service** | `QualityTrendService.generate_report()` |
| **Agent** | **Diana** (Documentation) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Trend analysis |
| **Processing** | Report generation, recommendations |
| **Output** | `report_markdown`, `recommendations[]` |
| **DB Table** | `quality_reports` |

---

### Step 5: Alert & Notify
**NOG TE DEFINIEREN EN TE PLANNEN**

> Deze stap wordt in een latere fase uitgewerkt. Zie Roadmap Phase 6.

---

## Database Schema

### quality_measurements
```sql
CREATE TABLE quality_measurements (
    id UUID PRIMARY KEY,
    application_id VARCHAR(50) REFERENCES application_registry(id),
    interval_type VARCHAR(20),  -- daily, weekly, monthly, quarterly, halfyearly, yearly
    status VARCHAR(20),  -- scheduled, running, completed, failed
    metrics_config JSONB,  -- Snapshot of app config at measurement time
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    triggered_by VARCHAR(50),  -- cron, manual, api
    created_at TIMESTAMP
);
```

### quality_snapshots
```sql
CREATE TABLE quality_snapshots (
    id UUID PRIMARY KEY,
    measurement_id UUID REFERENCES quality_measurements(id),
    application_id VARCHAR(50),
    snapshot_date DATE,
    interval_type VARCHAR(20),

    -- SIG TOP 10 + Security metrics (JSONB for flexibility)
    metrics JSONB,
    /*
    {
        "sig_volume": {"loc": 45000, "files": 234},
        "sig_duplication": {"percentage": 3.2, "blocks": 45},
        "sig_unit_size": {"avg_loc": 25, "over_threshold": 12},
        "sig_unit_complexity": {"avg": 6.5, "max": 32, "over_threshold": 8},
        "sig_unit_interfacing": {"avg_params": 3.1, "over_threshold": 5},
        "sig_module_coupling": {"fan_in_avg": 4.2, "fan_out_avg": 3.8},
        "sig_component_balance": {"gini": 0.35},
        "sig_component_independence": {"coupling_score": 0.42},
        "sig_code_comments": {"ratio": 0.12},
        "sig_test_coverage": {"line": 78.5, "branch": 65.2},
        "security": {"critical": 0, "high": 2, "medium": 5, "low": 12}
    }
    */

    -- Calculated scores (1-5 stars, SIG style)
    sig_scores JSONB,
    /*
    {
        "volume": 4,
        "duplication": 5,
        "unit_size": 3,
        "unit_complexity": 4,
        "overall_maintainability": 4
    }
    */

    raw_data JSONB,  -- Full analysis output for drill-down
    created_at TIMESTAMP
);

CREATE INDEX idx_snapshots_app_date ON quality_snapshots(application_id, snapshot_date);
CREATE INDEX idx_snapshots_interval ON quality_snapshots(interval_type, snapshot_date);
```

### quality_trends
```sql
CREATE TABLE quality_trends (
    id UUID PRIMARY KEY,
    measurement_id UUID REFERENCES quality_measurements(id),
    application_id VARCHAR(50),

    -- Comparison snapshots
    current_snapshot_id UUID REFERENCES quality_snapshots(id),
    previous_snapshot_id UUID REFERENCES quality_snapshots(id),

    -- Trend analysis
    trend_direction VARCHAR(20),  -- improving, stable, degrading, critical
    delta_metrics JSONB,  -- Percentage changes per metric
    threshold_violations JSONB,  -- Which thresholds exceeded
    anomalies JSONB,  -- Detected anomalies

    created_at TIMESTAMP
);
```

---

## Dashboard Integration

### Quality Trend Dashboard (NEW)

**File**: `quality-trend-dashboard.html`

```
┌─────────────────────────────────────────────────────────────────┐
│  QUALITY TREND DASHBOARD                    [App: MyApp ▼]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SIG Maintainability Score: ★★★★☆ (4/5)     vs vorige: ▲ +0.2  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Test Coverage│  │  Complexity  │  │  Duplication │           │
│  │    78.5%     │  │   Avg: 6.5   │  │     3.2%     │           │
│  │   ▲ +2.1%    │  │   ▼ +0.3    │  │   ▲ -0.5%    │           │
│  │  [PASS]      │  │  [PASS]      │  │  [PASS]      │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐                                                │
│  │  Security    │  Minimum Baseline Status: ✅ ALL PASS         │
│  │  0 critical  │                                                │
│  │  2 high      │                                                │
│  │  [PASS]      │                                                │
│  └──────────────┘                                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Maintainability Trend (12 months)                          ││
│  │  5★ ┤                           ╭────────────               ││
│  │  4★ ┤    ╭──────────────────────╯                           ││
│  │  3★ ┤───╯                                                    ││
│  │  2★ ┤                                                        ││
│  │     └─────────────────────────────────────────────────       ││
│  │       Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [Configure Metrics] [Run Manual Scan] [Download Report]        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow Navigation

### Entry Points
- **Scheduled**: Cron triggers at configured intervals
- **Manual**: Via API or dashboard button
- **From MAINTENANCE**: After maintenance cycle
- **Dashboard**: `quality-trend-dashboard.html`

### Output -> Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Trend Report | quality-trend-dashboard.html | → Review |
| Degrading Trend | maintenance-scheduler.html | → MAINTENANCE |
| Critical Threshold | kanban-dashboard.html | → BUG workflow |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/quality-trend/trigger` | Manual trigger measurement |
| GET | `/api/quality-trend/measurements` | List measurements |
| GET | `/api/quality-trend/measurements/{id}` | Get measurement details |
| GET | `/api/quality-trend/snapshots/{app_id}` | Get historical snapshots |
| GET | `/api/quality-trend/snapshots/{app_id}/latest` | Get latest snapshot |
| GET | `/api/quality-trend/trends/{app_id}` | Get trend analysis |
| GET | `/api/quality-trend/reports/{app_id}` | Get reports |
| GET | `/api/quality-trend/config/{app_id}` | Get app metric config |
| POST | `/api/quality-trend/config/{app_id}` | Set app metric config |
| GET | `/api/quality-trend/health` | Health check |

---

## Implementation Roadmap

### Phase 1: Foundation
- [ ] Database schema creation (quality_measurements, quality_snapshots, quality_trends)
- [ ] Application metric configuration table
- [ ] Basic API endpoints (trigger, config)
- [ ] Integration check with QUALITY_AUDIT

### Phase 2: Metric Collection (Hergebruik QUALITY_AUDIT)
- [x] Verify QUALITY_AUDIT has SIG TOP 10 metrics (Week 129: 8/10 geïmplementeerd)
- [x] Extend QUALITY_AUDIT - CommentsAnalyzer toegevoegd (Week 129)
- [ ] Unit Size analyzer toevoegen (#3)
- [ ] Component Independence analyzer toevoegen (#8)
- [ ] Implement metric collection service
- [ ] Snapshot storage

### Phase 3: Trend Analysis
- [ ] Rolling comparison algorithm
- [ ] Delta calculations
- [ ] Trend direction detection
- [ ] Threshold violation detection

### Phase 4: Dashboard
- [ ] quality-trend-dashboard.html
- [ ] SIG score visualization (stars)
- [ ] Trend charts (line, comparison)
- [ ] Metric configuration UI

### Phase 5: Automation
- [ ] Cron scheduling service
- [ ] Interval management
- [ ] Manual trigger from dashboard

### Phase 6: Alerting - NOG TE DEFINIEREN EN TE PLANNEN
- [ ] Alert threshold configuration
- [ ] Notification channels (Slack, Email, etc.)
- [ ] Alert history and management
- [ ] Escalation rules

---

## Hergebruik QUALITY_AUDIT

### Implementatiestatus (Week 129)

De QUALITY_AUDIT componenten zijn geverifieerd. Huidige status:

| # | SIG Metric | Analyzer | Status | Locatie |
|---|------------|----------|:------:|---------|
| 1 | **Volume** | `VolumeAnalyzer` | ✅ | `scanners/dotnet/volume_analyzer.py` |
| 2 | **Duplication** | `DuplicationAnalyzer` | ✅ | `scanners/metrics/duplication_analyzer.py` |
| 3 | **Unit Size** | - | ❌ | NOG TE IMPLEMENTEREN |
| 4 | **Unit Complexity** | `ComplexityAnalyzer` | ✅ | `scanners/metrics/complexity_analyzer.py` |
| 5 | **Unit Interfacing** | `InterfacingAnalyzer` | ✅ | `scanners/metrics/interfacing_analyzer.py` |
| 6 | **Module Coupling** | `CouplingAnalyzer` | ✅ | `scanners/metrics/coupling_analyzer.py` |
| 7 | **Component Balance** | `BalanceAnalyzer` | ✅ | `scanners/metrics/balance_analyzer.py` |
| 8 | **Component Independence** | - | ❌ | NOG TE IMPLEMENTEREN |
| 9 | **Code Comments** | `CommentsAnalyzer` | ✅ | `scanners/metrics/comments_analyzer.py` |
| 10 | **Test Coverage** | Test framework integration | ✅ | Via pytest-cov / dotCover |
| +1 | **Security** | GhostCrew integration | ✅ | `services/workflow_tool_integration_service.py` |

### Samenvatting

- **8/10 SIG metrics geïmplementeerd** (80%)
- **Minimum baseline: 6/6 metrics beschikbaar** ✅
- **Ontbrekend**: Unit Size (#3), Component Independence (#8)

### Minimum Baseline Status

Voor de **verplichte 6 minimum baseline metrics**:

| Metric | Status | Notes |
|--------|:------:|-------|
| Volume | ✅ | VolumeAnalyzer aanwezig |
| Duplication | ✅ | DuplicationAnalyzer aanwezig |
| Unit Complexity | ✅ | ComplexityAnalyzer aanwezig |
| Code Comments | ✅ | **CommentsAnalyzer toegevoegd Week 129** |
| Test Coverage | ✅ | Via pytest-cov / dotCover |
| Security | ✅ | Via GhostCrew integratie |

**Conclusie**: Alle minimum baseline metrics zijn beschikbaar. Quality Trend workflow kan gestart worden.

---

## Technical Infrastructure

This workflow uses shared infrastructure components. See [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) for details.

| Component | Used In Steps |
|-----------|---------------|
| AgentService | 2-4 (Quinn, Diana agents) |
| QualityAuditService | 2 (metric collection - hergebruik) |
| GraphWorkflowService | 2 (coupling analysis) |
| GhostCrew | 2 (security scanning) |
| Scheduler | 1 (cron triggers) |

---

## Relatie met Bestaande Workflows

| Workflow | Relatie |
|----------|---------|
| **QUALITY_AUDIT** | Quality Trend **hergebruikt** QUALITY_AUDIT componenten |
| MAINTENANCE | Degrading trends triggeren MAINTENANCE |
| BUG | Critical issues kunnen BUG workflow triggeren |

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Maintenance](./06-MAINTENANCE-DEBUG-WORKFLOWS.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
