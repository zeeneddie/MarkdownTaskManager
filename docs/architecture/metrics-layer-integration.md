# Metrics Layer Integration Specification

**Datum:** 2025-12-30
**Versie:** 1.0
**Status:** PLANNED (Week 126-127)
**Auteur:** MarQed AI Agent Platform

---

## Executive Summary

Integratie van de HCI-SoftwareKwaliteit-Migratie tools in het MarQed AI Agent Platform voor uitgebreide code quality metrics. Deze integratie voegt 4 nieuwe analyzers toe en verbetert 3 bestaande scanners met betere output en rating capabilities.

**Belangrijke beslissing:** Geen "SIG" terminologie gebruiken - dit heet "Metrics Layer".

---

## Bron Analyse

### HCI Tools Locatie

```
~/Projects/HCI-projecten/HCI-SoftwareKwaliteit-Migratie/tools/
├── 01-volume-analyzer/
├── 02-duplication-detector/    # READY - Type 1/2/3 werkend, duplicate reporting bug gefixed
├── 03-unit-complexity-analyzer/
├── 04-unit-interfacing-analyzer/
├── 05-module-coupling-analyzer/
├── 06-component-balance-analyzer/
├── 07-architecture-compliance-checker/
├── 08-library-security-scanner/
├── 09-github-overview/
└── master-orchestrator/
```

---

## Vergelijkingsmatrix

### Gedetailleerde Vergelijking

| Tool | HCI Features | MarQed Features | Beslissing | Reden |
|------|--------------|-----------------|------------|-------|
| **Volume Analyzer** | 14 extensions, 5-star rating, CSV/statistics | DotNetVolumeScanner: async, API, findings | **MERGE** | MarQed architectuur + HCI output |
| **Duplication Detector** | Type 1/2/3, Pareto stats | Hash-based Type 1 only | **MERGE** | HCI Type 1/2/3 werkt, bug gefixed (2025-12-30) |
| **Unit Complexity** | Cyclomatic per function | None | **ADD** | Nieuwe waarde |
| **Unit Interfacing** | Parameter count | None | **ADD** | Nieuwe waarde |
| **Module Coupling** | Fan-in/out, instability | None | **ADD** | Nieuwe waarde |
| **Component Balance** | Gini coefficient | None | **ADD** | Nieuwe waarde |
| **Architecture Compliance** | Layer violations | NEN7510/HIPAA/etc. | **EVALUATE** | Andere focus |
| **Library Security** | 8 libs, CVE, EOL | OWASP Top 10, 200+ patterns | **OPTIONAL** | MarQed beter, HCI EOL nuttig |
| **GitHub Overview** | LLM categorization | 6 analysis types | **OPTIONAL** | MarQed beter, HCI LLM nuttig |

---

## Implementatie Plan

### Week 126: Core Analyzers

#### ComplexityAnalyzer

```python
class ComplexityAnalyzer(BaseScanner):
    """
    Cyclomatic complexity analyzer per function.

    5-Star Rating:
    ★★★★★: avg < 10 (simple, maintainable)
    ★★★★☆: avg 10-15 (moderate complexity)
    ★★★☆☆: avg 15-20 (complex, refactor recommended)
    ★★☆☆☆: avg 20-25 (high risk)
    ★☆☆☆☆: avg > 25 (critical, immediate action needed)
    """

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'python', 'javascript']

    async def scan(self) -> ScanResult:
        # Implementatie
        pass
```

**Deliverables:**
- `backend/app/scanners/metrics/complexity_analyzer.py` (~300 LOC)
- Unit tests: 15 tests
- Integration met bestaande scanner registry

#### InterfacingAnalyzer

```python
class InterfacingAnalyzer(BaseScanner):
    """
    Parameter count analyzer per function.

    5-Star Rating:
    ★★★★★: avg < 4 parameters
    ★★★★☆: avg 4-5 parameters
    ★★★☆☆: avg 5-6 parameters
    ★★☆☆☆: avg 6-7 parameters
    ★☆☆☆☆: avg > 7 parameters
    """

    @property
    def name(self) -> str:
        return "interfacing"
```

**Deliverables:**
- `backend/app/scanners/metrics/interfacing_analyzer.py` (~250 LOC)
- Unit tests: 12 tests

#### CouplingAnalyzer

```python
class CouplingAnalyzer(BaseScanner):
    """
    Module coupling analyzer (fan-in, fan-out, instability).

    Instability Index = Fan-out / (Fan-in + Fan-out)

    5-Star Rating:
    ★★★★★: I < 0.3 (stable, low change risk)
    ★★★★☆: I 0.3-0.4
    ★★★☆☆: I 0.4-0.5
    ★★☆☆☆: I 0.5-0.7
    ★☆☆☆☆: I > 0.7 (unstable, high change propagation)
    """

    @property
    def name(self) -> str:
        return "coupling"
```

**Deliverables:**
- `backend/app/scanners/metrics/coupling_analyzer.py` (~350 LOC)
- Unit tests: 18 tests

#### BalanceAnalyzer

```python
class BalanceAnalyzer(BaseScanner):
    """
    Code distribution analyzer across components.
    Uses Gini coefficient for balance measurement.

    5-Star Rating:
    ★★★★★: Gini < 0.3 (well-balanced)
    ★★★★☆: Gini 0.3-0.4
    ★★★☆☆: Gini 0.4-0.5
    ★★☆☆☆: Gini 0.5-0.6
    ★☆☆☆☆: Gini > 0.6 (unbalanced, monolithic risk)
    """

    @property
    def name(self) -> str:
        return "balance"
```

**Deliverables:**
- `backend/app/scanners/metrics/balance_analyzer.py` (~300 LOC)
- Unit tests: 15 tests

#### VolumeScanner Upgrade

Upgrade bestaande `DotNetVolumeScanner`:

```python
# Toevoegen aan bestaande scanner:

def calculate_rating(self, metrics: ScanMetrics) -> int:
    """Calculate 5-star rating based on LOC thresholds."""
    code_lines = metrics.code_lines

    if code_lines < 66_000:
        return 5
    elif code_lines < 246_000:
        return 4
    elif code_lines < 655_000:
        return 3
    elif code_lines < 1_310_000:
        return 2
    else:
        return 1

def export_csv(self, result: ScanResult, path: str) -> None:
    """Export scan results to CSV."""
    pass

def export_excel(self, result: ScanResult, path: str) -> None:
    """Export scan results to Excel with statistics."""
    pass
```

**Deliverables:**
- Update `backend/app/scanners/dotnet/dotnet_scanner.py` (~100 LOC)
- Unit tests: 8 tests

#### DuplicationAnalyzer (NIEUW - 2025-12-30)

Integratie van HCI `code_clone_detector.py` met Type 1/2/3 support:

```python
class DuplicationAnalyzer(BaseScanner):
    """
    Code duplication analyzer with Type 1, 2, 3 clone detection.
    Based on HCI-SoftwareKwaliteit-Migratie/02-duplication-detector.

    Clone Types:
    - Type 1: Exact clones (identical code, whitespace ignored)
    - Type 2: Renamed clones (same structure, different identifiers)
    - Type 3: Near-miss clones (70% similarity threshold)

    5-Star Rating (based on duplication percentage):
    ★★★★★: ≤3% duplication
    ★★★★☆: 3-7% duplication
    ★★★☆☆: 7-10% duplication
    ★★☆☆☆: 10-20% duplication
    ★☆☆☆☆: >20% duplication
    """

    @property
    def name(self) -> str:
        return "duplication"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'python', 'javascript']

    async def scan(self) -> ScanResult:
        # Wrapper around HCI code_clone_detector
        pass
```

**Bron:** `/home/eddie/Projects/HCI-projecten/HCI-SoftwareKwaliteit-Migratie/tools/02-duplication-detector/code_clone_detector.py`

**Bug Fix (2025-12-30):** Duplicate reporting in CSV export verwijderd - Type 3 schrijft nu alleen nog 1 rij per paar i.p.v. 2 (A→B en B→A).

**Deliverables:**
- `backend/app/scanners/metrics/duplication_analyzer.py` (~400 LOC)
- Unit tests: 20 tests
- Integration met bestaande DotNetDuplicationScanner

#### CommentsAnalyzer (NIEUW - 2026-01-09)

Code Comments ratio analyzer voor SIG metric #9:

```python
class CommentsAnalyzer(BaseScanner):
    """
    Code comments ratio analyzer.
    Measures documentation coverage based on comment/code ratio.

    Comment Ratio = comment_lines / (comment_lines + code_lines) * 100

    5-Star Rating (higher is better - more comments = better documentation):
    ★★★★★: ratio >= 20% (excellent documentation)
    ★★★★☆: ratio 15-20% (good documentation)
    ★★★☆☆: ratio 10-15% (moderate documentation)
    ★★☆☆☆: ratio 5-10% (poor documentation)
    ★☆☆☆☆: ratio < 5% (minimal documentation)
    """

    @property
    def name(self) -> str:
        return "comments"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'python', 'javascript', 'typescript']

    async def scan(self) -> ScanResult:
        # Count comment vs code lines per file
        # Generate findings for poorly documented files
        pass
```

**Onderdeel van:** SIG TOP 10 Maintainability Model - Metric #9 (Code Comments)

**Minimum Baseline:** Ja - verplicht voor alle Quality Trend metingen

**Deliverables:**
- `backend/app/scanners/metrics/comments_analyzer.py` (~265 LOC) ✅ DONE
- Unit tests: 10-15 tests
- Integration met metrics scanner registry ✅ DONE

---

### Week 127: Integration Layer

#### Scanner Registry

```python
class MetricsScannerRegistry:
    """
    Central registry for all metrics scanners.
    Supports registration, discovery, and orchestration.
    """

    _scanners: Dict[str, Type[BaseScanner]] = {}

    @classmethod
    def register(cls, scanner_class: Type[BaseScanner]) -> None:
        """Register a scanner class."""
        cls._scanners[scanner_class.name] = scanner_class

    @classmethod
    def get_scanner(cls, name: str) -> Optional[Type[BaseScanner]]:
        """Get scanner by name."""
        return cls._scanners.get(name)

    @classmethod
    def scan_project(
        cls,
        project_path: str,
        scanners: List[str] = None
    ) -> Dict[str, ScanResult]:
        """Run multiple scanners on a project."""
        pass

    @classmethod
    def get_combined_rating(cls, results: Dict[str, ScanResult]) -> int:
        """Calculate overall project rating."""
        pass
```

**Deliverables:**
- `backend/app/scanners/registry.py` (~200 LOC)
- Unit tests: 10 tests

#### API Endpoints

```python
# backend/app/api/metrics.py

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

@router.get("/analyzers")
async def list_analyzers():
    """List all available analyzers with descriptions."""
    pass

@router.post("/scan/{project_id}")
async def run_scan(
    project_id: int,
    scanners: List[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Run full metrics scan on a project."""
    pass

@router.get("/scan/{scan_id}/results")
async def get_results(scan_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed scan results."""
    pass

@router.get("/scan/{scan_id}/rating")
async def get_rating(scan_id: int, db: AsyncSession = Depends(get_db)):
    """Get 5-star ratings per analyzer."""
    pass

@router.get("/scan/{scan_id}/export")
async def export_results(
    scan_id: int,
    format: str = "json",  # json, csv, excel
    db: AsyncSession = Depends(get_db)
):
    """Export scan results in specified format."""
    pass

@router.get("/projects/{project_id}/history")
async def get_history(
    project_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get historical metrics for a project."""
    pass

@router.get("/compare/{scan_id_1}/{scan_id_2}")
async def compare_scans(
    scan_id_1: int,
    scan_id_2: int,
    db: AsyncSession = Depends(get_db)
):
    """Compare two scans and show delta."""
    pass
```

**Deliverables:**
- `backend/app/api/metrics.py` (~300 LOC)
- Unit tests: 20 tests

#### Database Tables

```python
# backend/alembic/versions/059_add_metrics_layer_tables.py

class MetricsScan(Base):
    __tablename__ = "metrics_scans"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    overall_rating = Column(Integer)  # 1-5 stars
    status = Column(String)  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

class MetricsScanResult(Base):
    __tablename__ = "metrics_scan_results"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("metrics_scans.id"))
    analyzer_name = Column(String)  # complexity, coupling, etc.
    rating = Column(Integer)  # 1-5 stars
    metrics_json = Column(JSON)  # Analyzer-specific metrics
    findings_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class MetricsHistory(Base):
    __tablename__ = "metrics_history"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    scan_id = Column(Integer, ForeignKey("metrics_scans.id"))
    analyzer_name = Column(String)
    rating = Column(Integer)
    primary_metric_value = Column(Float)  # e.g., avg complexity
    snapshot_date = Column(Date)
```

#### Agent Integration

```python
# Quinn Quality Gate Integration

async def evaluate_metrics_quality_gate(
    project_id: int,
    min_rating: int = 3,
    db: AsyncSession = Depends(get_db)
) -> Tuple[List[str], List[str]]:
    """
    Evaluate metrics quality gate.

    Returns:
        Tuple of (blocking_issues, warnings)
    """
    blocking = []
    warnings = []

    # Get latest scan
    latest_scan = await get_latest_scan(project_id, db)

    for result in latest_scan.results:
        if result.rating < min_rating:
            blocking.append(
                f"{result.analyzer_name}: {result.rating}★ (minimum: {min_rating}★)"
            )
        elif result.rating == min_rating:
            warnings.append(
                f"{result.analyzer_name}: {result.rating}★ (borderline)"
            )

    return blocking, warnings
```

```python
# Miguel Migration Risk Integration

async def calculate_migration_risk_from_metrics(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculate migration risk based on metrics.

    High complexity + high coupling = high migration risk.
    """
    latest_scan = await get_latest_scan(project_id, db)

    complexity_rating = get_rating(latest_scan, "complexity")
    coupling_rating = get_rating(latest_scan, "coupling")

    # Risk calculation
    risk_score = (5 - complexity_rating) * 10 + (5 - coupling_rating) * 15

    return {
        "risk_score": risk_score,
        "risk_level": "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
        "complexity_factor": complexity_rating,
        "coupling_factor": coupling_rating,
        "recommendations": generate_recommendations(complexity_rating, coupling_rating)
    }
```

```python
# Eliza Estimation Integration

async def improve_estimation_with_metrics(
    project_id: int,
    base_fp: float,
    db: AsyncSession = Depends(get_db)
) -> float:
    """
    Adjust Function Point estimation based on code metrics.

    Higher complexity = more effort = higher adjusted FP.
    """
    latest_scan = await get_latest_scan(project_id, db)

    complexity_rating = get_rating(latest_scan, "complexity")
    coupling_rating = get_rating(latest_scan, "coupling")

    # Adjustment factor: 1.0 at 5 stars, 1.5 at 1 star
    complexity_factor = 1.0 + (5 - complexity_rating) * 0.125
    coupling_factor = 1.0 + (5 - coupling_rating) * 0.1

    adjusted_fp = base_fp * complexity_factor * coupling_factor

    return adjusted_fp
```

#### Metrics Dashboard

```html
<!-- frontend/metrics-dashboard.html -->
<!--
Dashboard features:
- Project selector
- Overall rating display (1-5 stars)
- Per-analyzer breakdown with trend charts
- Historical comparison
- Export buttons (CSV, Excel, JSON)
- Drill-down to individual file/function findings
-->
```

**Deliverables:**
- `frontend/metrics-dashboard.html` (~400 LOC)

---

## Optional Additions

### Security EOL Tracking

Voeg End-of-Life tracking toe aan bestaande `MigrationSecurityService`:

```python
# Toevoegen aan backend/app/services/migration_security_service.py

LIBRARY_EOL_DATABASE = {
    "jquery": {"eol_date": None, "latest": "3.7.1", "security_updates": True},
    "angularjs": {"eol_date": "2021-12-31", "latest": "1.8.3", "security_updates": False},
    "vue2": {"eol_date": "2023-12-31", "latest": "2.7.16", "security_updates": False},
    "react16": {"eol_date": None, "latest": "16.14.0", "security_updates": True},
    # etc.
}

async def check_library_eol(self, library: str, version: str) -> Dict[str, Any]:
    """Check if library version is end-of-life."""
    pass
```

### GitHub LLM Categorization

Voeg Ollama-based repository categorization toe aan `GitHubAnalysisService`:

```python
# Toevoegen aan backend/app/services/github_analysis_service.py

async def categorize_with_llm(
    self,
    repo_name: str,
    description: str,
    languages: List[str]
) -> Dict[str, Any]:
    """
    Use Ollama to categorize repository.

    Categories:
    - web_application
    - mobile_application
    - library
    - framework
    - tool
    - documentation
    - data_science
    - devops
    """
    prompt = f"""
    Categorize this repository:
    Name: {repo_name}
    Description: {description}
    Languages: {', '.join(languages)}

    Respond with a single category from: web_application, mobile_application,
    library, framework, tool, documentation, data_science, devops
    """

    response = await self.ollama_provider.generate(prompt)
    return {"category": response.strip().lower()}
```

---

## Success Criteria

| Criterium | Target | Meetbaar |
|-----------|--------|----------|
| **4 nieuwe analyzers** | ComplexityAnalyzer, InterfacingAnalyzer, CouplingAnalyzer, BalanceAnalyzer | ✅ Code aanwezig |
| **Volume upgrade** | 5-star rating + CSV/Excel export | ✅ Tests passing |
| **Scanner Registry** | Centraal beheer alle scanners | ✅ API working |
| **7 API endpoints** | Alle endpoints gedocumenteerd | ✅ OpenAPI spec |
| **Agent integratie** | Quinn, Miguel, Eliza | ✅ Integration tests |
| **Dashboard** | metrics-dashboard.html | ✅ UI functional |
| **LIM-001 resolved** | VB.NET parser via Metrics Layer | ✅ VB.NET files analyzed |

---

## Risico's en Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| HCI code quality issues | Medium | Medium | Code review, refactoring waar nodig |
| Performance op grote codebases | High | Low | Async processing, caching |
| Scanner incompatibiliteit | Medium | Low | BaseScanner protocol enforced |
| Missing VB.NET patterns | Medium | Medium | Start met bestaande HCI patterns |

---

## Tijdlijn

| Week | Focus | Deliverables |
|------|-------|--------------|
| **126 Day 1-2** | ComplexityAnalyzer | Scanner + 15 tests |
| **126 Day 3** | InterfacingAnalyzer | Scanner + 12 tests |
| **126 Day 4** | CouplingAnalyzer | Scanner + 18 tests |
| **126 Day 5** | BalanceAnalyzer + Volume upgrade | Scanners + 23 tests |
| **127 Day 1** | Scanner Registry | Registry + 10 tests |
| **127 Day 2-3** | API Endpoints | 7 endpoints + 20 tests |
| **127 Day 4** | Agent Integration | Quinn/Miguel/Eliza integration |
| **127 Day 5** | Dashboard + Documentation | UI + docs |

---

## Referenties

- **HCI Tools Source:** `~/Projects/HCI-projecten/HCI-SoftwareKwaliteit-Migratie/tools/`
- **Bestaande Scanners:** `backend/app/scanners/dotnet/`
- **Base Scanner Protocol:** `backend/app/scanners/base.py`
- **Agent Services:** `backend/app/services/agent_service.py`

---

**Last Updated:** 2025-12-30
**Approved By:** -
**Implementation Start:** Week 126
