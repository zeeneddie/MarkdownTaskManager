# Complete Gap Analysis & Implementation Roadmap
# Marqed Legacy Modernization Platform

> **Document Version**: 1.0
> **Created**: Week 144 (January 2026)
> **Total Gaps**: 72 items
> **Estimated Duration**: 130 weken (~2.5 jaar)
> **Excluded Items**: 6 (C3, C7, C8, I7, H2, I3)

---

## Executive Summary

Dit document bevat de complete gap-analyse en implementatie-roadmap voor het Marqed platform, gebaseerd op analyse van:
- 6 Nederlandse legacy modernisatie consultancies
- 5 GitHub repositories
- 1 technische gist
- Vergelijking met huidige Marqed capabilities

### Fase Overzicht

| Fase | Focus | Duur | Items | Business Value |
|------|-------|------|-------|----------------|
| 1 | Quick Wins & Foundation | 12 weken | 15 | Sales acceleratie, Security basis |
| 2 | Core Platform Enhancement | 16 weken | 18 | Enterprise-ready platform |
| 3 | AI & Automation | 14 weken | 12 | Differentiatie, Efficiency |
| 4 | Testing Excellence | 10 weken | 8 | Kwaliteitsgarantie |
| 5 | Advanced Integrations | 12 weken | 10 | Ecosystem uitbreiding |
| 6 | Innovation & Scale | 16 weken | 9 | Market leadership |

---

## Scoring Methodology

### ROI Score Berekening
```
ROI = (Business Value × Prioriteit) / (Tijd × Complexiteit) × 2
```

### Score Definities

| Score | Prioriteit | Tijd (weken) | Business Value | Complexiteit |
|-------|------------|--------------|----------------|--------------|
| 1 | Laag | 1-2 | Minimaal | Eenvoudig |
| 2 | Medium-Laag | 2-4 | Beperkt | Gemiddeld |
| 3 | Medium | 4-6 | Significant | Complex |
| 4 | Medium-Hoog | 6-10 | Hoog | Zeer complex |
| 5 | Kritiek | 10+ | Transformatief | Expert nodig |

---

# FASE 1: QUICK WINS & FOUNDATION
## Weken 1-12 | 15 Items | Focus: Sales & Security

### Rationale
Deze fase focust op items met hoogste ROI die direct business value opleveren:
- Versnelling van sales cycle
- Security differentiatie
- Basis tooling voor alle volgende fases

---

## A1: Legacy Quickscan
**Categorie**: Assessment & Sales | **ROI**: 8.0 | **Bron**: PAQT

### Beschrijving
Snelle 15-minuten geautomatiseerde assessment tool die een Go/No-Go beslissing geeft voor legacy modernisatie projecten.

### Functionele Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| A1.1 | Automatische code upload en analyse | Must |
| A1.2 | Technologie stack detectie | Must |
| A1.3 | Complexity score berekening | Must |
| A1.4 | Risk assessment (0-100) | Must |
| A1.5 | Go/No-Go recommendation | Must |
| A1.6 | PDF rapport generatie | Must |
| A1.7 | Vergelijking met benchmark database | Should |
| A1.8 | Effort estimation (rough) | Should |

### Technische Specificatie
```python
class LegacyQuickscan:
    """
    15-minute automated legacy assessment.
    """

    def __init__(self):
        self.analyzers = [
            TechnologyDetector(),
            ComplexityAnalyzer(),
            DependencyScanner(),
            SecurityRiskAssessor(),
            CodeQualityChecker()
        ]

    async def scan(self,
                   source_path: str,
                   config: QuickscanConfig) -> QuickscanReport:
        """
        Execute quickscan and return report.
        Target: < 15 minutes for 100K LOC
        """
        results = await asyncio.gather(*[
            analyzer.analyze(source_path)
            for analyzer in self.analyzers
        ])

        return QuickscanReport(
            technology_stack=results[0],
            complexity_score=results[1].score,
            dependency_count=results[2].total,
            security_risks=results[3].findings,
            code_quality=results[4].metrics,
            recommendation=self._calculate_recommendation(results),
            estimated_effort=self._estimate_effort(results)
        )

    def _calculate_recommendation(self, results) -> Recommendation:
        score = sum(r.score for r in results) / len(results)
        if score >= 70:
            return Recommendation.GO
        elif score >= 40:
            return Recommendation.CONDITIONAL
        else:
            return Recommendation.NO_GO
```

### Database Schema
```sql
CREATE TABLE quickscan_reports (
    id UUID PRIMARY KEY,
    project_name VARCHAR(255),
    scan_date TIMESTAMP,
    technology_stack JSONB,
    complexity_score INTEGER,
    risk_score INTEGER,
    recommendation VARCHAR(50),
    report_pdf_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints
```
POST /api/v1/quickscan/upload
POST /api/v1/quickscan/analyze/{scan_id}
GET  /api/v1/quickscan/report/{scan_id}
GET  /api/v1/quickscan/report/{scan_id}/pdf
```

### UI Components
- Upload wizard (drag & drop)
- Progress indicator met real-time status
- Interactive report dashboard
- PDF download button

### Acceptance Criteria
- [ ] Scan compleet binnen 15 minuten voor 100K LOC
- [ ] Rapport bevat alle 5 analyse dimensies
- [ ] PDF export functioneel
- [ ] 95% accuracy op technologie detectie

### Effort Estimate
| Task | Tijd |
|------|------|
| Backend services | 1.5 week |
| Analyzers integratie | 1 week |
| API endpoints | 0.5 week |
| UI components | 1 week |
| Testing | 0.5 week |
| **Totaal** | **4.5 weken** |

---

## K3: Secret Detection
**Categorie**: Security & Compliance | **ROI**: 8.0 | **Bron**: awesome-legacy

### Beschrijving
Automatische detectie van hardcoded credentials, API keys, passwords en andere secrets in legacy code.

### Functionele Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| K3.1 | Detectie van 50+ secret patterns | Must |
| K3.2 | Support voor alle legacy talen | Must |
| K3.3 | False positive filtering | Must |
| K3.4 | Severity classificatie | Must |
| K3.5 | Remediation suggestions | Should |
| K3.6 | Git history scanning | Should |
| K3.7 | CI/CD integration | Should |

### Secret Patterns
```python
SECRET_PATTERNS = {
    # API Keys
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "aws_secret_key": r"[0-9a-zA-Z/+]{40}",
    "azure_storage": r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+",
    "google_api": r"AIza[0-9A-Za-z-_]{35}",

    # Database
    "connection_string": r"(Server|Data Source)=[^;]+;.*(Password|Pwd)=[^;]+",
    "mongodb_uri": r"mongodb(\+srv)?://[^:]+:[^@]+@",

    # Authentication
    "jwt_secret": r"(jwt|JWT).*(secret|SECRET|key|KEY)\s*[=:]\s*['\"][^'\"]+['\"]",
    "oauth_secret": r"(client_secret|CLIENT_SECRET)\s*[=:]\s*['\"][^'\"]+['\"]",

    # Generic
    "password_field": r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    "private_key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    "basic_auth": r"Basic\s+[A-Za-z0-9+/=]{20,}",
}
```

### Technische Specificatie
```python
class SecretDetector:
    """
    Scans code for hardcoded secrets and credentials.
    """

    def __init__(self):
        self.patterns = self._load_patterns()
        self.entropy_threshold = 4.5
        self.false_positive_filter = FalsePositiveFilter()

    def scan_file(self, file_path: str) -> List[SecretFinding]:
        findings = []
        content = self._read_file(file_path)

        for line_num, line in enumerate(content.split('\n'), 1):
            # Pattern matching
            for name, pattern in self.patterns.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    finding = SecretFinding(
                        file_path=file_path,
                        line_number=line_num,
                        secret_type=name,
                        matched_text=self._mask_secret(match.group()),
                        severity=self._assess_severity(name),
                        confidence=self._calculate_confidence(match, line)
                    )
                    if not self.false_positive_filter.is_false_positive(finding):
                        findings.append(finding)

            # High entropy detection (catch unknown patterns)
            if self._calculate_entropy(line) > self.entropy_threshold:
                findings.extend(self._analyze_high_entropy(line, line_num, file_path))

        return findings

    def _assess_severity(self, secret_type: str) -> SeverityLevel:
        critical_types = ["private_key", "aws_secret_key", "connection_string"]
        high_types = ["password_field", "jwt_secret", "oauth_secret"]

        if secret_type in critical_types:
            return SeverityLevel.CRITICAL
        elif secret_type in high_types:
            return SeverityLevel.HIGH
        return SeverityLevel.MEDIUM
```

### Database Schema
```sql
CREATE TABLE secret_findings (
    id UUID PRIMARY KEY,
    scan_id UUID REFERENCES scans(id),
    file_path TEXT,
    line_number INTEGER,
    secret_type VARCHAR(100),
    masked_value TEXT,
    severity VARCHAR(20),
    confidence FLOAT,
    remediated BOOLEAN DEFAULT FALSE,
    remediation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_secret_severity ON secret_findings(severity);
CREATE INDEX idx_secret_scan ON secret_findings(scan_id);
```

### API Endpoints
```
POST /api/v1/security/secrets/scan
GET  /api/v1/security/secrets/findings/{scan_id}
PUT  /api/v1/security/secrets/findings/{id}/remediate
GET  /api/v1/security/secrets/report/{scan_id}
```

### Acceptance Criteria
- [ ] Detecteert 95%+ van bekende secret patterns
- [ ] False positive rate < 5%
- [ ] Scan 100K LOC binnen 2 minuten
- [ ] Severity correct geclassificeerd

### Effort Estimate
| Task | Tijd |
|------|------|
| Pattern engine | 1 week |
| False positive filter | 0.5 week |
| API & database | 0.5 week |
| Testing & tuning | 0.5 week |
| **Totaal** | **2.5 weken** |

---

## A2: Fixed-Price Templates
**Categorie**: Assessment & Sales | **ROI**: 7.0 | **Bron**: Codeless

### Beschrijving
Contract templates met transparante risicoverdeling voor fixed-price legacy modernisatie projecten.

### Functionele Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| A2.1 | Template generator | Must |
| A2.2 | Risk matrix calculator | Must |
| A2.3 | Milestone definitions | Must |
| A2.4 | Change request procedures | Must |
| A2.5 | Acceptance criteria templates | Should |
| A2.6 | SLA templates | Should |

### Template Structure
```markdown
## FIXED-PRICE LEGACY MODERNIZATION CONTRACT

### 1. Project Scope
- Source System: [AUTO-FILLED from Quickscan]
- Target Platform: [SELECTED]
- Estimated LOC: [AUTO-FILLED]
- Complexity Score: [AUTO-FILLED]

### 2. Pricing Model
| Component | Fixed Price | Risk Buffer |
|-----------|-------------|-------------|
| Analysis Phase | €X | 10% |
| Development Phase | €Y | 15% |
| Testing Phase | €Z | 10% |
| Migration Phase | €W | 20% |
| **Total** | **€T** | **15% avg** |

### 3. Risk Allocation Matrix
| Risk Category | Client | Vendor | Shared |
|---------------|--------|--------|--------|
| Scope creep | | | ✓ |
| Technical complexity | | ✓ | |
| Data quality | ✓ | | |
| Timeline delays | | | ✓ |

### 4. Milestones & Payment Schedule
[AUTO-GENERATED based on project size]

### 5. Change Request Procedure
[STANDARD TEMPLATE]
```

### Effort Estimate: 2 weken

---

## B9: UI Wrapper - Field Mapper
**Categorie**: AI & Automatisering | **ROI**: 7.5 | **Bron**: Nieuw concept

### Beschrijving
Configureerbare mapping tussen nieuwe UI velden en legacy UI velden, inclusief transformaties en validaties.

### Functionele Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| B9.1 | Visual field mapper interface | Must |
| B9.2 | JSON configuration export | Must |
| B9.3 | Field transformations | Must |
| B9.4 | Composite field support | Must |
| B9.5 | Validation rules | Should |
| B9.6 | Live preview | Should |

### Configuration Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FieldMapperConfig",
  "type": "object",
  "properties": {
    "screen_id": { "type": "string" },
    "legacy_url": { "type": "string", "format": "uri" },
    "mode": {
      "type": "string",
      "enum": ["frontend", "backend", "both"]
    },
    "fields": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "new_field": { "type": "string" },
          "legacy_selector": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["text", "number", "select", "checkbox", "date", "composite"]
          },
          "transform": { "type": "string" },
          "validation": { "type": "string" },
          "value_map": { "type": "object" }
        },
        "required": ["new_field", "legacy_selector", "type"]
      }
    },
    "actions": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "legacy_trigger": { "type": "string" },
          "wait_for": { "type": "string" },
          "timeout": { "type": "integer" }
        }
      }
    }
  }
}
```

### Technische Specificatie
```typescript
interface FieldMapper {
  // Map new field value to legacy field(s)
  mapToLegacy(field: string, value: any): LegacyMapping[];

  // Map legacy field value to new field
  mapFromLegacy(selector: string, value: any): NewFieldValue;

  // Apply transformation
  transform(value: any, transformer: string): any;

  // Validate field value
  validate(field: string, value: any): ValidationResult;
}

class FieldMapperService implements FieldMapper {
  private config: FieldMapperConfig;
  private transformers: Map<string, Transformer>;

  constructor(config: FieldMapperConfig) {
    this.config = config;
    this.transformers = new Map([
      ['lowercase', (v) => v.toLowerCase()],
      ['uppercase', (v) => v.toUpperCase()],
      ['trim', (v) => v.trim()],
      ['date_nl', (v) => this.formatDateNL(v)],
      ['currency_eur', (v) => this.formatCurrency(v, 'EUR')],
    ]);
  }

  mapToLegacy(field: string, value: any): LegacyMapping[] {
    const fieldConfig = this.config.fields.find(f => f.new_field === field);
    if (!fieldConfig) throw new Error(`Field ${field} not configured`);

    // Handle composite fields
    if (fieldConfig.type === 'composite') {
      return this.mapCompositeField(fieldConfig, value);
    }

    // Apply transformation
    let transformedValue = value;
    if (fieldConfig.transform) {
      transformedValue = this.transform(value, fieldConfig.transform);
    }

    // Apply value mapping for selects
    if (fieldConfig.value_map && fieldConfig.value_map[transformedValue]) {
      transformedValue = fieldConfig.value_map[transformedValue];
    }

    return [{
      selector: fieldConfig.legacy_selector,
      value: transformedValue,
      type: fieldConfig.type
    }];
  }
}
```

### Effort Estimate: 3 weken

---

## E1: Visuele DLL Dependency Map
**Categorie**: Architecture Analyse | **ROI**: 6.5 | **Bron**: Dependencies

### Beschrijving
Interactieve graaf visualisatie van DLL dependencies met zoom, filter en export mogelijkheden.

### Functionele Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| E1.1 | Force-directed graph layout | Must |
| E1.2 | Zoom en pan controls | Must |
| E1.3 | Filter op dependency type | Must |
| E1.4 | Node clustering | Should |
| E1.5 | Export naar PNG/SVG | Should |
| E1.6 | Dependency path highlighting | Should |

### Technische Stack
- **Frontend**: D3.js of Cytoscape.js
- **Backend**: Python networkx voor graph processing
- **Database**: Neo4j of PostgreSQL met recursive CTE's

### Effort Estimate: 2 weken

---

## E2: Circular Dependency Detector
**Categorie**: Architecture Analyse | **ROI**: 6.5 | **Bron**: Dependencies

### Beschrijving
Automatische detectie van circulaire dependencies met visualisatie van de cycles.

### Algorithm
```python
def detect_circular_dependencies(graph: DependencyGraph) -> List[Cycle]:
    """
    Tarjan's algorithm for finding strongly connected components.
    """
    cycles = []
    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    on_stack = {}

    def strongconnect(node):
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack[node] = True

        for successor in graph.get_dependencies(node):
            if successor not in index:
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif on_stack.get(successor, False):
                lowlinks[node] = min(lowlinks[node], index[successor])

        if lowlinks[node] == index[node]:
            component = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == node:
                    break
            if len(component) > 1:
                cycles.append(Cycle(nodes=component))

    for node in graph.nodes:
        if node not in index:
            strongconnect(node)

    return cycles
```

### Effort Estimate: 2 weken

---

## E7: Technical Debt Heatmap
**Categorie**: Architecture Analyse | **ROI**: 6.5 | **Bron**: PAQT

### Beschrijving
Visuele heatmap die technische schuld per module/bestand toont.

### Metrics voor Heatmap
| Metric | Weight | Calculation |
|--------|--------|-------------|
| Cyclomatic Complexity | 25% | McCabe metric |
| Code Duplication | 20% | Clone detection |
| Test Coverage | 20% | Inverse coverage |
| Dependency Count | 15% | In/out degree |
| Age Since Last Change | 10% | Days dormant |
| Bug History | 10% | Defect density |

### Effort Estimate: 2 weken

---

## G3: API Gateway Templates
**Categorie**: Migratie Patterns | **ROI**: 6.5 | **Bron**: LinkIT

### Beschrijving
REST facade templates voor legacy systemen met standaard patterns voor authentication, rate limiting en caching.

### Template Types
1. **Simple Proxy**: Direct doorsturen
2. **Aggregator**: Meerdere legacy calls combineren
3. **Transformer**: Request/response transformatie
4. **Cached**: Met caching layer

### Effort Estimate: 2 weken

---

## J2: Performance Baseline Tool
**Categorie**: Monitoring | **ROI**: 6.5 | **Bron**: Netrom

### Beschrijving
Tool voor het vastleggen van performance baselines voor legacy systemen als referentie voor migratie.

### Metrics
- Response times (p50, p95, p99)
- Throughput (requests/second)
- Resource usage (CPU, memory, I/O)
- Database query times
- External service latencies

### Effort Estimate: 2 weken

---

## J6: Health Check Suite
**Categorie**: Monitoring | **ROI**: 6.5 | **Bron**: Netrom

### Beschrijving
Post-migratie validatie suite die functionele en non-functionele requirements controleert.

### Check Categories
- Functional parity checks
- Data integrity validation
- Performance comparison
- Security posture verification
- Integration health

### Effort Estimate: 2 weken

---

## K1: Legacy Vulnerability Scanner
**Categorie**: Security | **ROI**: 6.5 | **Bron**: awesome-legacy

### Beschrijving
Scanner voor bekende vulnerabilities in legacy code en dependencies.

### Vulnerability Sources
- CVE database
- OWASP Top 10
- CWE patterns
- Vendor advisories
- Custom rules voor legacy patterns

### Effort Estimate: 3 weken

---

## K4: Security Debt Calculator
**Categorie**: Security | **ROI**: 6.5 | **Bron**: PAQT

### Beschrijving
Kwantificering van security risico's in financiele termen.

### Calculation Model
```
Security Debt = Σ (Vulnerability_Severity × Exposure_Factor × Asset_Value)
```

### Effort Estimate: 2 weken

---

## A4: Modernisatie Strategie Selector
**Categorie**: Assessment & Sales | **ROI**: 6.5 | **Bron**: PAQT

### Beschrijving
Wizard die helpt bij het selecteren van de juiste modernisatie strategie (Rebuild, Refactor, Replace, etc.)

### Decision Tree
```
START
├── Is business logic valuable?
│   ├── YES: Is codebase maintainable?
│   │   ├── YES: REFACTOR
│   │   └── NO: Is documentation available?
│   │       ├── YES: REBUILD
│   │       └── NO: REWRITE with domain experts
│   └── NO: Is COTS available?
│       ├── YES: REPLACE
│       └── NO: RETIRE or REBUILD minimal
```

### Effort Estimate: 2 weken

---

## H8: Project Export Suite (NIEUW)
**Categorie**: Documentatie | **ROI**: 4.5 | **Bron**: User Request

### Beschrijving
Uitgebreide export mogelijkheden voor project planning data naar diverse formaten.

### Supported Formats
| Format | Extension | Use Case |
|--------|-----------|----------|
| CSV | .csv | Spreadsheets, data analysis |
| Excel | .xlsx | Microsoft Excel met formatting |
| LibreOffice Calc | .ods | Open source spreadsheet |
| OpenProject XML | .xml | OpenProject import |
| LibrePlan XML | .xml | LibrePlan import |
| MS Project | .mpp/.xml | Microsoft Project compatible |

### Technische Specificatie
```python
class ProjectExportService:
    """
    Export project data to multiple formats.
    """

    def __init__(self):
        self.exporters = {
            'csv': CSVExporter(),
            'xlsx': ExcelExporter(),
            'ods': LibreOfficeExporter(),
            'openproject': OpenProjectXMLExporter(),
            'libreplan': LibrePlanXMLExporter(),
            'msproject': MSProjectExporter(),
        }

    def export(self,
               project_data: ProjectData,
               format: str,
               options: ExportOptions = None) -> bytes:
        """
        Export project data to specified format.
        """
        exporter = self.exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")

        return exporter.export(project_data, options)

    def export_roadmap(self,
                       roadmap: RoadmapData,
                       format: str) -> bytes:
        """
        Export roadmap with phases, items, dependencies.
        """
        project_data = self._convert_roadmap_to_project(roadmap)
        return self.export(project_data, format)


class OpenProjectXMLExporter:
    """
    Export to OpenProject XML format.
    """

    def export(self, data: ProjectData, options: ExportOptions) -> bytes:
        root = ET.Element('openproject')

        # Project metadata
        project = ET.SubElement(root, 'project')
        ET.SubElement(project, 'name').text = data.name
        ET.SubElement(project, 'identifier').text = data.identifier

        # Work packages (tasks)
        work_packages = ET.SubElement(root, 'work_packages')
        for task in data.tasks:
            wp = ET.SubElement(work_packages, 'work_package')
            ET.SubElement(wp, 'subject').text = task.name
            ET.SubElement(wp, 'type').text = task.type
            ET.SubElement(wp, 'status').text = task.status
            ET.SubElement(wp, 'estimated_hours').text = str(task.hours)
            ET.SubElement(wp, 'start_date').text = task.start_date
            ET.SubElement(wp, 'due_date').text = task.due_date

            # Dependencies
            if task.dependencies:
                relations = ET.SubElement(wp, 'relations')
                for dep in task.dependencies:
                    rel = ET.SubElement(relations, 'relation')
                    ET.SubElement(rel, 'type').text = 'follows'
                    ET.SubElement(rel, 'to_id').text = dep

        return ET.tostring(root, encoding='unicode')
```

### API Endpoints
```
GET  /api/v1/export/formats                    # List available formats
POST /api/v1/export/project/{id}               # Export project
POST /api/v1/export/roadmap/{id}               # Export roadmap
POST /api/v1/export/gap-analysis/{id}          # Export gap analysis
GET  /api/v1/export/download/{export_id}       # Download exported file
```

### Effort Estimate: 3 weken

---

## Fase 1 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| A1 | Legacy Quickscan | 4.5 | - |
| K3 | Secret Detection | 2.5 | - |
| A2 | Fixed-Price Templates | 2 | A1 |
| B9 | UI Wrapper Field Mapper | 3 | - |
| E1 | DLL Dependency Map | 2 | - |
| E2 | Circular Dependency Detector | 2 | E1 |
| E7 | Technical Debt Heatmap | 2 | - |
| G3 | API Gateway Templates | 2 | - |
| J2 | Performance Baseline | 2 | - |
| J6 | Health Check Suite | 2 | - |
| K1 | Vulnerability Scanner | 3 | K3 |
| K4 | Security Debt Calculator | 2 | K1 |
| A4 | Strategie Selector | 2 | A1 |
| **H8** | **Project Export Suite (NIEUW)** | **3** | - |
| **TOTAAL** | | **34 weken werk** | |

> **Note**: Met parallel development (3 teams) is Fase 1 in 12 weken te realiseren.

---

---

# FASE 2: CORE PLATFORM ENHANCEMENT
## Weken 13-28 | 18 Items | Focus: Enterprise-Ready Platform

### Rationale
Bouw voort op Fase 1 foundation met robuuste platform capabilities voor enterprise klanten.

---

## B8: UI Wrapper - Headless Automation
**Categorie**: AI & Automatisering | **ROI**: 6.5 | **Bron**: legacy-use concept

### Beschrijving
Nieuwe UI die legacy UI headless bestuurt via Playwright/Puppeteer, gebruiker ziet alleen moderne interface.

### Technische Specificatie
```typescript
class HeadlessLegacyAutomation {
  private browser: Browser;
  private page: Page;
  private fieldMapper: FieldMapperService;

  async initialize(legacyUrl: string): Promise<void> {
    this.browser = await playwright.chromium.launch({ headless: true });
    this.page = await this.browser.newPage();
    await this.page.goto(legacyUrl);
  }

  async fillForm(formData: Record<string, any>): Promise<void> {
    for (const [field, value] of Object.entries(formData)) {
      const mappings = this.fieldMapper.mapToLegacy(field, value);
      for (const mapping of mappings) {
        await this.fillLegacyField(mapping);
      }
    }
  }

  private async fillLegacyField(mapping: LegacyMapping): Promise<void> {
    const element = await this.page.$(mapping.selector);
    if (!element) throw new Error(`Element ${mapping.selector} not found`);

    switch (mapping.type) {
      case 'text':
        await element.fill(mapping.value);
        break;
      case 'select':
        await element.selectOption(mapping.value);
        break;
      case 'checkbox':
        if (mapping.value) await element.check();
        else await element.uncheck();
        break;
      case 'date':
        await this.fillDatePicker(element, mapping.value);
        break;
    }
  }

  async submitForm(actionName: string): Promise<SubmitResult> {
    const action = this.fieldMapper.getAction(actionName);
    await this.page.click(action.legacy_trigger);

    if (action.wait_for) {
      await this.page.waitForSelector(action.wait_for, {
        timeout: action.timeout || 5000
      });
    }

    return this.captureResult();
  }

  async captureScreenshot(): Promise<Buffer> {
    return await this.page.screenshot();
  }
}
```

### API Endpoints
```
POST /api/v1/ui-wrapper/session/create
POST /api/v1/ui-wrapper/session/{id}/navigate
POST /api/v1/ui-wrapper/session/{id}/fill
POST /api/v1/ui-wrapper/session/{id}/submit
GET  /api/v1/ui-wrapper/session/{id}/screenshot
DELETE /api/v1/ui-wrapper/session/{id}
```

### Effort Estimate: 4 weken

---

## B10: UI Wrapper - Dual Mode
**Categorie**: AI & Automatisering | **ROI**: 6.5 | **Bron**: Nieuw concept

### Beschrijving
Toggle functionaliteit: alleen backend / alleen frontend / beide modes.

### Mode Definitions
```typescript
enum WrapperMode {
  LEGACY_ONLY = 'legacy_only',      // Geen wrapper actief
  FRONTEND_WRAP = 'frontend_wrap',  // Nieuwe UI → Legacy backend
  BACKEND_WRAP = 'backend_wrap',    // Legacy UI → Nieuwe backend
  FULL_WRAP = 'full_wrap',          // Nieuwe UI → Nieuwe backend (met legacy fallback)
  HYBRID = 'hybrid'                 // Per-feature configureerbaar
}

interface DualModeConfig {
  defaultMode: WrapperMode;
  featureOverrides: Map<string, WrapperMode>;
  fallbackEnabled: boolean;
  fallbackThreshold: number; // Error rate before fallback
}
```

### Effort Estimate: 2 weken

---

## J5: Rollback Automation
**Categorie**: Monitoring | **ROI**: 6.0 | **Bron**: Netrom

### Beschrijving
Automatische rollback naar legacy bij failures met configureerbare thresholds.

### Technische Specificatie
```python
class RollbackAutomation:
    def __init__(self, config: RollbackConfig):
        self.error_threshold = config.error_threshold  # e.g., 5%
        self.latency_threshold = config.latency_threshold  # e.g., 2x baseline
        self.health_check_interval = config.health_check_interval

    async def monitor_and_rollback(self,
                                   new_system: SystemEndpoint,
                                   legacy_system: SystemEndpoint):
        metrics = await self.collect_metrics(new_system)

        if self.should_rollback(metrics):
            await self.execute_rollback(legacy_system)
            await self.notify_team(RollbackEvent(
                reason=self.determine_reason(metrics),
                metrics=metrics,
                timestamp=datetime.now()
            ))

    def should_rollback(self, metrics: SystemMetrics) -> bool:
        return (
            metrics.error_rate > self.error_threshold or
            metrics.p99_latency > self.latency_threshold or
            not metrics.health_check_passed
        )
```

### Effort Estimate: 3 weken

---

## D6: Spring Boot Templates
**Categorie**: Target Platforms | **ROI**: 5.5 | **Bron**: Legacy-Mod-Agents

### Beschrijving
Production-ready Spring Boot templates voor Java migratie targets.

### Template Variants
1. **spring-boot-rest-api**: REST API met OpenAPI
2. **spring-boot-batch**: Batch processing
3. **spring-boot-integration**: Enterprise integration patterns
4. **spring-boot-reactive**: WebFlux reactive stack

### Effort Estimate: 3 weken

---

## G1: Adapter Pattern Library
**Categorie**: Migratie Patterns | **ROI**: 5.5 | **Bron**: legacy-systems

### Beschrijving
Herbruikbare adapter implementaties voor common legacy integratie patterns.

### Adapter Types
```java
// Interface adapter
public interface LegacyAdapter<TLegacy, TNew> {
    TNew fromLegacy(TLegacy legacy);
    TLegacy toLegacy(TNew modern);
}

// Database adapter
public class LegacyDatabaseAdapter implements LegacyAdapter<ResultSet, Entity> {
    // Maps old column names to new entity fields
}

// Service adapter
public class LegacySoapAdapter implements LegacyAdapter<SoapMessage, RestRequest> {
    // Converts SOAP to REST and vice versa
}

// File format adapter
public class LegacyFileAdapter implements LegacyAdapter<FixedWidthRecord, JsonObject> {
    // Converts fixed-width files to JSON
}
```

### Effort Estimate: 3 weken

---

## K2: Compliance Mapping
**Categorie**: Security | **ROI**: 5.5 | **Bron**: Codeless

### Beschrijving
GDPR/SOX/HIPAA requirement tracking gedurende migratie.

### Compliance Matrix
| Requirement | Legacy Status | Migration Impact | New Status | Evidence |
|-------------|---------------|------------------|------------|----------|
| GDPR Art. 17 (Right to erasure) | Partial | High | Full | [Link] |
| SOX 404 (Internal controls) | Full | Medium | Full | [Link] |

### Effort Estimate: 3 weken

---

## K6: Audit Trail Generator
**Categorie**: Security | **ROI**: 5.5 | **Bron**: Codeless

### Beschrijving
Automatische generatie van compliance documentatie voor audits.

### Generated Documents
- Change log met approvals
- Data flow diagrams
- Access control matrices
- Test evidence reports
- Risk assessment updates

### Effort Estimate: 2 weken

---

## J4: Migration Progress Dashboard
**Categorie**: Monitoring | **ROI**: 5.5 | **Bron**: Codeless

### Beschrijving
Real-time dashboard met migratie voortgang per module/feature.

### Dashboard Components
```typescript
interface MigrationDashboard {
  overallProgress: ProgressBar;       // 0-100%
  phaseProgress: PhaseBreakdown[];    // Per fase
  moduleStatus: ModuleStatusGrid;     // Per module RAG status
  burndownChart: BurndownChart;       // Remaining work
  riskRadar: RiskRadarChart;          // Current risks
  teamVelocity: VelocityChart;        // Story points/week
  blockersList: BlockersList;         // Active blockers
}
```

### Effort Estimate: 3 weken

---

## E5: Impact Analyse Dashboard
**Categorie**: Architecture | **ROI**: 5.0 | **Bron**: Netrom

### Beschrijving
Voorspelling van wijzigingsimpact voordat changes worden doorgevoerd.

### Analysis Engine
```python
class ImpactAnalyzer:
    def analyze_change(self,
                       changed_components: List[str],
                       dependency_graph: DependencyGraph) -> ImpactReport:
        directly_affected = set()
        indirectly_affected = set()

        for component in changed_components:
            # Direct dependents
            dependents = dependency_graph.get_dependents(component)
            directly_affected.update(dependents)

            # Transitive dependents (2 levels)
            for dependent in dependents:
                indirectly_affected.update(
                    dependency_graph.get_dependents(dependent)
                )

        return ImpactReport(
            changed=changed_components,
            direct_impact=list(directly_affected),
            indirect_impact=list(indirectly_affected - directly_affected),
            risk_score=self._calculate_risk(directly_affected, indirectly_affected),
            suggested_test_scope=self._suggest_tests(directly_affected)
        )
```

### Effort Estimate: 3 weken

---

## E6: Architecture Decision Records
**Categorie**: Architecture | **ROI**: 5.0 | **Bron**: awesome-legacy

### Beschrijving
Automatische ADR generator voor migratie beslissingen.

### ADR Template
```markdown
# ADR-{NUMBER}: {TITLE}

## Status
{Proposed | Accepted | Deprecated | Superseded}

## Context
{What is the issue that we're seeing that is motivating this decision?}

## Decision
{What is the change that we're proposing and/or doing?}

## Consequences
{What becomes easier or more difficult to do because of this change?}

## Alternatives Considered
{What other options were evaluated?}

## Related ADRs
{Links to related decisions}
```

### Effort Estimate: 2 weken

---

## G5: Database Sync Patterns
**Categorie**: Migratie Patterns | **ROI**: 5.0 | **Bron**: Netrom

### Beschrijving
Dual-write en sync strategies voor database migraties.

### Patterns
1. **Dual Write**: Write to both, read from new
2. **CDC (Change Data Capture)**: Stream changes from legacy
3. **ETL Batch**: Periodic sync
4. **Event Sourcing Bridge**: Event-driven sync

### Effort Estimate: 3 weken

---

## G8: Anti-Corruption Layer
**Categorie**: Migratie Patterns | **ROI**: 5.0 | **Bron**: LinkIT

### Beschrijving
DDD Anti-Corruption Layer templates voor bounded context isolation.

### Implementation
```python
class AntiCorruptionLayer:
    """
    Translates between legacy domain model and new domain model.
    Protects new system from legacy complexity.
    """

    def __init__(self,
                 legacy_adapter: LegacyAdapter,
                 domain_translator: DomainTranslator):
        self.legacy_adapter = legacy_adapter
        self.translator = domain_translator

    def get_customer(self, customer_id: str) -> Customer:
        # Get from legacy
        legacy_customer = self.legacy_adapter.get_customer(customer_id)

        # Translate to new domain model
        return self.translator.to_new_customer(legacy_customer)

    def save_customer(self, customer: Customer) -> None:
        # Translate to legacy model
        legacy_customer = self.translator.to_legacy_customer(customer)

        # Save to legacy
        self.legacy_adapter.save_customer(legacy_customer)
```

### Effort Estimate: 3 weken

---

## F1: Seam Model Implementation
**Categorie**: Testing | **ROI**: 5.0 | **Bron**: Gist

### Beschrijving
Implementatie van Michael Feathers' Seam Model voor change point identificatie.

### Seam Types
```python
class SeamFinder:
    """
    Identifies seams (places where behavior can be changed without editing code).
    """

    def find_seams(self, code: str, language: str) -> List[Seam]:
        seams = []

        # Object seams (dependency injection points)
        seams.extend(self.find_object_seams(code))

        # Preprocessing seams (macros, includes)
        seams.extend(self.find_preprocessing_seams(code))

        # Link seams (library boundaries)
        seams.extend(self.find_link_seams(code))

        return seams

    def find_object_seams(self, code: str) -> List[ObjectSeam]:
        """Find constructor injection and method parameter injection points."""
        # Pattern: new ClassName() or CreateObject()
        pass
```

### Effort Estimate: 3 weken

---

## F5: Golden Master Testing
**Categorie**: Testing | **ROI**: 5.0 | **Bron**: awesome-legacy

### Beschrijving
Capture and compare output baseline voor legacy system behavior.

### Implementation
```python
class GoldenMasterTest:
    def __init__(self, legacy_system: LegacySystem):
        self.legacy = legacy_system
        self.golden_masters: Dict[str, GoldenMaster] = {}

    def capture_baseline(self,
                         test_case: TestCase,
                         inputs: Dict[str, Any]) -> GoldenMaster:
        """Capture legacy system output as baseline."""
        output = self.legacy.execute(test_case.endpoint, inputs)

        golden = GoldenMaster(
            test_case_id=test_case.id,
            inputs=inputs,
            expected_output=output,
            captured_at=datetime.now()
        )
        self.golden_masters[test_case.id] = golden
        return golden

    def verify_against_baseline(self,
                                new_system: NewSystem,
                                test_case: TestCase,
                                inputs: Dict[str, Any]) -> VerificationResult:
        """Compare new system output against golden master."""
        golden = self.golden_masters[test_case.id]
        actual_output = new_system.execute(test_case.endpoint, inputs)

        return VerificationResult(
            passed=self._compare_outputs(golden.expected_output, actual_output),
            expected=golden.expected_output,
            actual=actual_output,
            differences=self._find_differences(golden.expected_output, actual_output)
        )
```

### Effort Estimate: 3 weken

---

## H3: Interactive Documentation
**Categorie**: Documentatie | **ROI**: 5.0 | **Bron**: LinkIT

### Beschrijving
Swagger/OpenAPI documentatie met try-it-out functionaliteit.

### Features
- Auto-generated from code annotations
- Interactive API explorer
- Code samples in multiple languages
- Authentication integration

### Effort Estimate: 2 weken

---

## H4: Migration Playbooks
**Categorie**: Documentatie | **ROI**: 5.0 | **Bron**: Codeless

### Beschrijving
Step-by-step guides voor verschillende migratie scenarios.

### Playbook Types
1. **VB6 to .NET Core**: Complete migration guide
2. **Classic ASP to Python/Django**: Web app migration
3. **COBOL to Java**: Mainframe modernization
4. **Database Migration**: Oracle to PostgreSQL
5. **API Modernization**: SOAP to REST

### Effort Estimate: 2 weken

---

## C4: PL/SQL Diepere Analyse
**Categorie**: Taal Support | **ROI**: 5.0 | **Bron**: Netrom

### Beschrijving
Uitgebreide analyse van Oracle PL/SQL stored procedures.

### Analysis Capabilities
- Procedure/function dependency mapping
- Business logic extraction
- Performance anti-patterns detection
- Migration complexity scoring

### Effort Estimate: 3 weken

---

## A7: Cost Anomaly Detection (NIEUW)
**Categorie**: Assessment & Sales | **ROI**: 4.0 | **Bron**: User Request

### Beschrijving
AI-powered detectie van budget overschrijdingen en cost anomalies tijdens migratie projecten.

### Features
| Feature | Beschrijving |
|---------|--------------|
| Cost Prediction | ML-based voorspelling van project kosten |
| Anomaly Detection | Real-time detectie van onverwachte kosten |
| Budget Alerts | Configureerbare alerts bij threshold breach |
| Optimization Tips | AI-gegenereerde besparingsadviezen |
| Trend Analysis | Historische cost trend analyse |

### Technische Specificatie
```python
class CostAnomalyDetector:
    """
    Detect cost anomalies and predict budget issues.
    """

    def __init__(self):
        self.model = load_model('cost_prediction_model')
        self.threshold_multiplier = 1.5  # 50% above baseline = anomaly

    def predict_cost(self,
                     project_data: ProjectData,
                     historical_data: List[HistoricalProject]) -> CostPrediction:
        """
        Predict project cost based on characteristics.
        """
        features = self._extract_features(project_data)
        similar_projects = self._find_similar_projects(features, historical_data)

        prediction = self.model.predict(features)
        confidence = self._calculate_confidence(similar_projects)

        return CostPrediction(
            estimated_cost=prediction,
            confidence=confidence,
            range_low=prediction * 0.8,
            range_high=prediction * 1.3,
            similar_projects=similar_projects[:5]
        )

    def detect_anomalies(self,
                         actual_costs: List[CostEntry],
                         baseline: CostBaseline) -> List[CostAnomaly]:
        """
        Detect anomalies in actual vs expected costs.
        """
        anomalies = []

        for entry in actual_costs:
            expected = baseline.get_expected(entry.category, entry.date)
            if entry.amount > expected * self.threshold_multiplier:
                anomalies.append(CostAnomaly(
                    entry=entry,
                    expected=expected,
                    deviation=(entry.amount - expected) / expected,
                    severity=self._assess_severity(entry, expected),
                    recommendation=self._generate_recommendation(entry)
                ))

        return anomalies

    def generate_optimization_tips(self,
                                    project: ProjectData) -> List[OptimizationTip]:
        """
        AI-generated cost saving recommendations.
        """
        tips = []

        # Analyze spending patterns
        patterns = self._analyze_patterns(project.cost_history)

        # Resource optimization
        if patterns.has_idle_resources:
            tips.append(OptimizationTip(
                category='resources',
                potential_savings=patterns.idle_resource_cost,
                recommendation='Scale down idle resources during non-peak hours'
            ))

        # License optimization
        if patterns.has_unused_licenses:
            tips.append(OptimizationTip(
                category='licenses',
                potential_savings=patterns.unused_license_cost,
                recommendation='Review and cancel unused license subscriptions'
            ))

        return tips
```

### Alert Configuration
```yaml
cost_alerts:
  budget_threshold:
    warning: 80%    # Alert at 80% of budget
    critical: 95%   # Critical at 95%

  anomaly_detection:
    sensitivity: medium  # low, medium, high
    window: 7d           # Detection window

  notifications:
    channels:
      - email
      - slack
      - dashboard
    recipients:
      - project_manager
      - finance_team
```

### Effort Estimate: 3 weken

---

## Fase 2 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| B8 | UI Wrapper Headless | 4 | B9 |
| B10 | UI Wrapper Dual Mode | 2 | B8 |
| J5 | Rollback Automation | 3 | J2, J6 |
| D6 | Spring Boot Templates | 3 | - |
| G1 | Adapter Pattern Library | 3 | - |
| K2 | Compliance Mapping | 3 | - |
| K6 | Audit Trail Generator | 2 | K2 |
| J4 | Migration Progress Dashboard | 3 | - |
| E5 | Impact Analyse Dashboard | 3 | E1, E2 |
| E6 | ADR Generator | 2 | - |
| G5 | Database Sync Patterns | 3 | - |
| G8 | Anti-Corruption Layer | 3 | G1 |
| F1 | Seam Model | 3 | - |
| F5 | Golden Master Testing | 3 | - |
| H3 | Interactive Documentation | 2 | - |
| H4 | Migration Playbooks | 2 | - |
| C4 | PL/SQL Analyse | 3 | - |
| **A7** | **Cost Anomaly Detection (NIEUW)** | **3** | A1 |
| **TOTAAL** | | **50 weken werk** | |

> **Note**: Met parallel development (3 teams) is Fase 2 in 16 weken te realiseren.

---

---

# FASE 3: AI & AUTOMATION
## Weken 29-42 | 12 Items | Focus: Differentiatie & Efficiency

### Rationale
Implementeer AI-gedreven capabilities die Marqed onderscheiden van concurrentie.

---

## B1: AI Legacy Access (VNC/RDP)
**Categorie**: AI & Automatisering | **ROI**: 6.0 | **Bron**: legacy-use

### Beschrijving
Real-time legacy interactie via AI + VNC/RDP zonder code changes aan legacy systeem.

### Technische Architectuur
```
┌─────────────────────────────────────────────────────────────┐
│                    AI LEGACY ACCESS                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │ Claude  │ ──► │ Action      │ ──► │ VNC/RDP        │   │
│  │ API     │     │ Interpreter │     │ Controller     │   │
│  └─────────┘     └─────────────┘     └────────┬────────┘   │
│                                               │             │
│                                               ▼             │
│                                      ┌─────────────────┐   │
│                                      │ Legacy System   │   │
│                                      │ (Windows/AS400) │   │
│                                      └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation
```python
class AILegacyAccess:
    def __init__(self):
        self.llm = ClaudeClient()
        self.vnc = VNCController()
        self.action_parser = ActionParser()

    async def execute_task(self, task_description: str) -> TaskResult:
        """
        Execute task on legacy system using AI vision and control.
        """
        # Capture current screen
        screenshot = await self.vnc.capture_screen()

        # Ask AI to analyze and determine actions
        analysis = await self.llm.analyze_screen(
            screenshot=screenshot,
            task=task_description,
            context=self.get_context()
        )

        # Execute actions
        for action in analysis.actions:
            await self.execute_action(action)
            await asyncio.sleep(0.5)  # Wait for UI update

            # Verify action succeeded
            new_screenshot = await self.vnc.capture_screen()
            if not await self.llm.verify_action(action, new_screenshot):
                return TaskResult(success=False, error="Action verification failed")

        return TaskResult(success=True, data=self.extract_result())

    async def execute_action(self, action: LegacyAction):
        match action.type:
            case "click":
                await self.vnc.click(action.x, action.y)
            case "type":
                await self.vnc.type_text(action.text)
            case "key":
                await self.vnc.send_key(action.key)
            case "scroll":
                await self.vnc.scroll(action.direction, action.amount)
```

### Effort Estimate: 5 weken

---

## B2: COBOL Parser & Analyzer
**Categorie**: AI & Automatisering | **ROI**: 5.5 | **Bron**: Legacy-Mod-Agents

### Beschrijving
COBOL code analyse met business rule extractie.

### Parser Features
- Division/Section parsing (IDENTIFICATION, ENVIRONMENT, DATA, PROCEDURE)
- COPYBOOK resolution
- Paragraph flow analysis
- Data hierarchy extraction
- PERFORM/CALL graph

### Effort Estimate: 4 weken

---

## B3: COBOL → Java Generator
**Categorie**: AI & Automatisering | **ROI**: 5.0 | **Bron**: Legacy-Mod-Agents

### Beschrijving
AI-powered COBOL naar Java code conversie.

### Mapping Rules
| COBOL | Java |
|-------|------|
| WORKING-STORAGE | Class fields |
| COPYBOOK | Import class |
| PARAGRAPH | Method |
| PERFORM | Method call |
| MOVE | Assignment |
| IF/EVALUATE | if/switch |
| COMPUTE | Expression |

### Effort Estimate: 5 weken

---

## B7: Natural Language Query
**Categorie**: AI & Automatisering | **ROI**: 4.5 | **Bron**: legacy-use

### Beschrijving
Query legacy systeem in natuurlijke taal (Nederlands/Engels).

### Example Queries
```
User: "Geef me alle klanten uit Amsterdam met openstaande facturen"
System: SELECT * FROM Customers c
        JOIN Invoices i ON c.id = i.customer_id
        WHERE c.city = 'Amsterdam' AND i.status = 'open'

User: "Toon de omzet per maand van vorig jaar"
System: [Navigates to reports, selects date range, exports data]
```

### Effort Estimate: 4 weken

---

## B6: AI Code Review
**Categorie**: AI & Automatisering | **ROI**: 4.0 | **Bron**: Cube.nl

### Beschrijving
Automated code quality feedback via LLM analyse.

### Review Categories
- Code smells detection
- Security vulnerabilities
- Performance issues
- Best practice violations
- Migration readiness assessment

### Effort Estimate: 3 weken

---

## B11: UI Wrapper - AI Form Filler
**Categorie**: AI & Automatisering | **ROI**: 5.5 | **Bron**: Nieuw concept

### Beschrijving
AI herkent automatisch legacy form velden en mappt naar nieuwe UI.

### Auto-Detection
```python
class AIFormFieldDetector:
    async def detect_fields(self, screenshot: bytes) -> List[DetectedField]:
        """
        Use vision AI to detect and classify form fields.
        """
        analysis = await self.llm.analyze_image(
            image=screenshot,
            prompt="""
            Identify all form fields in this screenshot.
            For each field, provide:
            - Bounding box coordinates
            - Field type (text, dropdown, checkbox, etc.)
            - Label text
            - Current value (if any)
            - Probable data type (name, email, phone, date, etc.)
            """
        )

        return [
            DetectedField(
                bounds=f.bounds,
                field_type=f.type,
                label=f.label,
                value=f.value,
                semantic_type=f.semantic_type
            )
            for f in analysis.fields
        ]
```

### Effort Estimate: 4 weken

---

## E3: Process Mining
**Categorie**: Architecture | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
Runtime gedrag analyse van legacy processen.

### Features
- Event log extraction
- Process discovery
- Conformance checking
- Bottleneck identification

### Effort Estimate: 5 weken

---

## E4: Data Lineage Visualisatie
**Categorie**: Architecture | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
Visuele weergave van data flow door legacy systeem.

### Lineage Tracking
```
Source Table → Transform → Intermediate → Transform → Target Table
     ↓              ↓            ↓             ↓            ↓
  [Schema]    [Business    [Validation]   [Mapping]   [New Schema]
              Rule #12]
```

### Effort Estimate: 4 weken

---

## G2: Side-by-Side Execution Framework
**Categorie**: Migratie Patterns | **ROI**: 4.5 | **Bron**: legacy-systems

### Beschrijving
Framework voor het draaien van legacy en nieuw systeem naast elkaar.

### Modes
1. **Shadow Mode**: New reads, legacy writes (verify new)
2. **Mirror Mode**: Both write, compare results
3. **Canary Mode**: % traffic to new, rest to legacy
4. **Cutover Mode**: New primary, legacy fallback

### Effort Estimate: 4 weken

---

## G6: Feature Toggle Framework
**Categorie**: Migratie Patterns | **ROI**: 4.5 | **Bron**: LinkIT

### Beschrijving
Gradual feature rollout met runtime toggles.

### Toggle Types
- Release toggles (deploy vs release)
- Experiment toggles (A/B testing)
- Ops toggles (kill switch)
- Permission toggles (user segments)

### Effort Estimate: 2 weken

---

## G7: Circuit Breaker Patterns
**Categorie**: Migratie Patterns | **ROI**: 4.5 | **Bron**: LinkIT

### Beschrijving
Resilience patterns voor legacy integraties.

### States
```
CLOSED ──[failures > threshold]──► OPEN
   ▲                                  │
   │                                  │
   └────[success]──── HALF-OPEN ◄────┘
                      [timeout]
```

### Effort Estimate: 2 weken

---

## A3: TCO Calculator
**Categorie**: Assessment & Sales | **ROI**: 5.5 | **Bron**: Netrom

### Beschrijving
Total Cost of Ownership berekening tool voor legacy vs modern.

### Cost Categories
| Category | Legacy Costs | Migration Costs | New System Costs |
|----------|--------------|-----------------|------------------|
| Hosting | Monthly | One-time | Monthly |
| Maintenance | Annual | Project | Annual |
| Support | Per incident | Training | Per incident |
| Licenses | Annual | Migration tools | Annual |
| Opportunity | Lost business | Project risk | Growth enabled |

### Effort Estimate: 3 weken

---

## B12: LLM Agent Collaboration Framework (NIEUW)
**Categorie**: AI & Automatisering | **ROI**: 4.5 | **Bron**: User Requirement

### Beschrijving
Framework voor meerdere LLM agents die samenwerken aan analyse en migratie taken. Humans zijn ALLEEN betrokken bij review en escalaties.

### Agent Types
| Agent | Rol | Specialisatie |
|-------|-----|---------------|
| **Analyzer Agent** | Code analyse | Pattern detection, complexity scoring |
| **Extractor Agent** | Business logic | Rule extraction, data flow |
| **Generator Agent** | Code generatie | Target code, tests, docs |
| **Reviewer Agent** | Kwaliteit | Code review, best practices |
| **Validator Agent** | Verificatie | Output validation, regression check |
| **Coordinator Agent** | Orchestratie | Task distribution, conflict resolution |

### Human-in-the-Loop Protocol
```python
class HumanInLoopProtocol:
    """
    Defines when and how humans are involved.
    Humans ONLY review, they don't do real-time work.
    """

    # Escalation triggers
    ESCALATION_TRIGGERS = {
        'confidence_threshold': 0.7,      # Below 70% confidence → escalate
        'conflict_detected': True,         # Agents disagree → escalate
        'security_decision': True,         # Security-related → escalate
        'business_rule_ambiguity': True,   # Unclear business logic → escalate
        'cost_threshold_exceeded': True,   # Major cost implications → escalate
    }

    def should_escalate(self, context: AgentContext) -> EscalationDecision:
        """
        Determine if human review is needed.
        """
        if context.confidence < self.ESCALATION_TRIGGERS['confidence_threshold']:
            return EscalationDecision(
                escalate=True,
                reason='low_confidence',
                required_action='review_and_approve'
            )

        if context.has_conflicting_results:
            return EscalationDecision(
                escalate=True,
                reason='agent_conflict',
                required_action='resolve_conflict'
            )

        if context.is_security_related:
            return EscalationDecision(
                escalate=True,
                reason='security_decision',
                required_action='security_review'
            )

        return EscalationDecision(escalate=False)
```

### Agent Collaboration Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM AGENT COLLABORATION FRAMEWORK                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    COORDINATOR AGENT                         │   │
│  │  • Task distribution                                         │   │
│  │  • Conflict resolution                                       │   │
│  │  • Progress tracking                                         │   │
│  └─────────────────────┬───────────────────────────────────────┘   │
│                        │                                            │
│          ┌─────────────┼─────────────┐                             │
│          ▼             ▼             ▼                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                        │
│  │ ANALYZER  │ │ EXTRACTOR │ │ GENERATOR │                        │
│  │  Agent    │ │   Agent   │ │   Agent   │                        │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                        │
│        │             │             │                                │
│        └─────────────┼─────────────┘                               │
│                      ▼                                              │
│              ┌───────────┐                                         │
│              │ REVIEWER  │                                         │
│              │   Agent   │                                         │
│              └─────┬─────┘                                         │
│                    │                                                │
│                    ▼                                                │
│              ┌───────────┐                                         │
│              │ VALIDATOR │                                         │
│              │   Agent   │                                         │
│              └─────┬─────┘                                         │
│                    │                                                │
│     ┌──────────────┴──────────────┐                                │
│     ▼                             ▼                                 │
│  ┌─────────┐              ┌─────────────┐                          │
│  │ OUTPUT  │              │  ESCALATION │                          │
│  │ (Auto)  │              │  (Human)    │                          │
│  └─────────┘              └─────────────┘                          │
│                                  │                                  │
│                                  ▼                                  │
│                           ┌───────────┐                            │
│                           │  HUMAN    │                            │
│                           │  REVIEW   │ ◄── ONLY reviews,          │
│                           │  QUEUE    │     no real-time work      │
│                           └───────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Communication Protocol
```python
class AgentMessage:
    """
    Message format for agent-to-agent communication.
    """
    sender: str           # Agent ID
    recipient: str        # Agent ID or 'broadcast'
    message_type: str     # 'request', 'response', 'result', 'conflict'
    content: Dict         # Payload
    confidence: float     # 0.0 - 1.0
    timestamp: datetime
    correlation_id: str   # For tracking conversations


class AgentCollaborationService:
    """
    Orchestrates collaboration between LLM agents.
    """

    def __init__(self):
        self.agents = {
            'analyzer': AnalyzerAgent(),
            'extractor': ExtractorAgent(),
            'generator': GeneratorAgent(),
            'reviewer': ReviewerAgent(),
            'validator': ValidatorAgent(),
            'coordinator': CoordinatorAgent(),
        }
        self.message_queue = MessageQueue()
        self.escalation_handler = HumanInLoopProtocol()

    async def execute_task(self, task: MigrationTask) -> TaskResult:
        """
        Execute migration task with agent collaboration.
        """
        # Phase 1: Analysis
        analysis = await self.agents['analyzer'].analyze(task.source_code)

        # Phase 2: Extraction
        extraction = await self.agents['extractor'].extract(
            code=task.source_code,
            analysis=analysis
        )

        # Phase 3: Generation
        generated = await self.agents['generator'].generate(
            extraction=extraction,
            target_platform=task.target
        )

        # Phase 4: Review
        review = await self.agents['reviewer'].review(generated)

        # Check for conflicts or low confidence
        if review.has_issues or review.confidence < 0.7:
            # Let agents try to resolve
            resolution = await self._resolve_internally(review)

            if not resolution.resolved:
                # Escalate to human
                return await self._escalate_to_human(task, review)

        # Phase 5: Validation
        validation = await self.agents['validator'].validate(
            original=task.source_code,
            generated=generated
        )

        return TaskResult(
            success=validation.passed,
            output=generated,
            confidence=validation.confidence,
            human_review_required=False
        )
```

### Effort Estimate: 4 weken

---

## Fase 3 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| B1 | AI Legacy Access | 5 | B8, B9 |
| B2 | COBOL Parser | 4 | - |
| B3 | COBOL → Java | 5 | B2 |
| B7 | NL Query | 4 | B1 |
| B6 | AI Code Review | 3 | - |
| B11 | AI Form Filler | 4 | B8, B9 |
| E3 | Process Mining | 5 | - |
| E4 | Data Lineage | 4 | E1 |
| G2 | Side-by-Side | 4 | G1 |
| G6 | Feature Toggles | 2 | - |
| G7 | Circuit Breaker | 2 | - |
| A3 | TCO Calculator | 3 | A1 |
| **B12** | **LLM Agent Collaboration (NIEUW)** | **4** | B5, B6 |
| **TOTAAL** | | **49 weken werk** | |

> **Note**: Met parallel development (3 teams) is Fase 3 in 16 weken te realiseren.

---

# FASE 4: TESTING EXCELLENCE
## Weken 43-52 | 8 Items | Focus: Kwaliteitsgarantie

### Rationale
Complete testing framework voor migratie validatie.

---

## F2: Sprout Method Generator
**Categorie**: Testing | **ROI**: 4.5 | **Bron**: Gist

### Beschrijving
Generator voor nieuwe methodes in legacy code (Feathers pattern).

### Pattern
```python
# Before: Monolithic method
def process_order(order):
    # 500 lines of code
    pass

# After: Sprout method
def process_order(order):
    # ... existing code ...
    new_discount = calculate_loyalty_discount(order)  # Sprouted!
    # ... existing code ...

def calculate_loyalty_discount(order):  # New, testable method
    if order.customer.loyalty_years > 5:
        return order.total * 0.1
    return 0
```

### Effort Estimate: 2 weken

---

## F3: Sprout Class Generator
**Categorie**: Testing | **ROI**: 4.5 | **Bron**: Gist

### Beschrijving
Generator voor nieuwe classes rond legacy code.

### Effort Estimate: 2 weken

---

## F4: Wrap Method Templates
**Categorie**: Testing | **ROI**: 4.5 | **Bron**: Gist

### Beschrijving
Templates voor method wrapping patterns.

### Effort Estimate: 2 weken

---

## F6: Mutation Testing Integratie
**Categorie**: Testing | **ROI**: 4.0 | **Bron**: awesome-legacy

### Beschrijving
Test quality validatie via mutation testing.

### Tools Integration
- Stryker (JavaScript/TypeScript)
- Stryker.NET (C#)
- PIT (Java)
- mutmut (Python)

### Effort Estimate: 3 weken

---

## F7: Contract Testing
**Categorie**: Testing | **ROI**: 4.5 | **Bron**: LinkIT

### Beschrijving
API backward compatibility validatie.

### Tools
- Pact for consumer-driven contracts
- OpenAPI diff for schema changes
- Custom validators for legacy APIs

### Effort Estimate: 2 weken

---

## F8: Visual Regression Testing
**Categorie**: Testing | **ROI**: 4.0 | **Bron**: Netrom

### Beschrijving
UI screenshot comparison framework.

### Workflow
1. Capture legacy UI screenshots
2. Capture new UI screenshots
3. Pixel-by-pixel comparison
4. Highlight differences
5. Approve or reject changes

### Effort Estimate: 3 weken

---

## J1: Dual-System Monitoring
**Categorie**: Monitoring | **ROI**: 5.0 | **Bron**: Netrom

### Beschrijving
Compare metrics between legacy and new system in real-time.

### Metrics Compared
- Response times (side by side)
- Error rates (delta)
- Throughput (comparison)
- Resource usage (efficiency)

### Effort Estimate: 3 weken

---

## J3: Log Correlation Engine
**Categorie**: Monitoring | **ROI**: 3.0 | **Bron**: LinkIT

### Beschrijving
Cross-system log tracing met correlation IDs.

### Features
- Distributed tracing
- Log aggregation
- Search and filter
- Alerting rules

### Effort Estimate: 4 weken

---

## Fase 4 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| F2 | Sprout Method | 2 | F1 |
| F3 | Sprout Class | 2 | F1 |
| F4 | Wrap Method | 2 | F1 |
| F6 | Mutation Testing | 3 | - |
| F7 | Contract Testing | 2 | - |
| F8 | Visual Regression | 3 | - |
| J1 | Dual Monitoring | 3 | J2 |
| J3 | Log Correlation | 4 | - |
| **TOTAAL** | | **21 weken werk** | |

> **Note**: Met parallel development (2 teams) is Fase 4 in 10 weken te realiseren.

---

# FASE 5: ADVANCED INTEGRATIONS
## Weken 53-64 | 10 Items | Focus: Ecosystem Uitbreiding

---

## D1: Mendix Export
**Categorie**: Target Platforms | **ROI**: 3.5 | **Bron**: LinkIT

### Beschrijving
Export naar Mendix low-code platform.

### Export Features
- Domain model generation
- Microflow scaffolding
- Page templates
- Integration stubs

### Effort Estimate: 4 weken

---

## D2: OutSystems Export
**Categorie**: Target Platforms | **ROI**: 3.5 | **Bron**: LinkIT

### Beschrijving
Export naar OutSystems low-code platform.

### Effort Estimate: 4 weken

---

## D3: Flowable BPM Integratie
**Categorie**: Target Platforms | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
BPMN process export naar Flowable.

### Effort Estimate: 3 weken

---

## D4: Camunda BPM Integratie
**Categorie**: Target Platforms | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
BPMN process export naar Camunda.

### Effort Estimate: 3 weken

---

## D7: Kubernetes Deployment
**Categorie**: Target Platforms | **ROI**: 3.5 | **Bron**: XTi

### Beschrijving
Kubernetes manifests en Helm charts generator.

### Effort Estimate: 4 weken

---

## D8: Azure DevOps Pipeline
**Categorie**: Target Platforms | **ROI**: 4.5 | **Bron**: Netrom

### Beschrijving
CI/CD pipeline templates voor Azure DevOps.

### Effort Estimate: 2 weken

---

## I1: AWS Migration Templates
**Categorie**: Cloud & Infra | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
CloudFormation/CDK templates voor AWS migratie.

### Effort Estimate: 3 weken

---

## I2: Azure ARM Templates
**Categorie**: Cloud & Infra | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
Azure Resource Manager templates.

### Effort Estimate: 3 weken

---

## I4: Terraform Modules
**Categorie**: Cloud & Infra | **ROI**: 4.5 | **Bron**: XTi

### Beschrijving
Multi-cloud Terraform modules.

### Effort Estimate: 3 weken

---

## I5: Database Migration Service
**Categorie**: Cloud & Infra | **ROI**: 4.5 | **Bron**: Netrom

### Beschrijving
Managed database migration tooling integratie.

### Supported Migrations
- Oracle → PostgreSQL
- SQL Server → PostgreSQL
- MySQL → PostgreSQL
- Access → PostgreSQL

### Effort Estimate: 4 weken

---

## Fase 5 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| D1 | Mendix Export | 4 | - |
| D2 | OutSystems Export | 4 | - |
| D3 | Flowable BPM | 3 | E3 |
| D4 | Camunda BPM | 3 | E3 |
| D7 | Kubernetes | 4 | - |
| D8 | Azure DevOps | 2 | - |
| I1 | AWS Templates | 3 | - |
| I2 | Azure Templates | 3 | - |
| I4 | Terraform | 3 | - |
| I5 | DB Migration | 4 | - |
| **TOTAAL** | | **33 weken werk** | |

> **Note**: Met parallel development (3 teams) is Fase 5 in 12 weken te realiseren.

---

# FASE 6: INNOVATION & SCALE
## Weken 65-80 | 9 Items | Focus: Market Leadership

---

## C1: COBOL Volledige Support
**Categorie**: Taal Support | **ROI**: 5.5 | **Bron**: Legacy-Mod-Agents

### Beschrijving
Complete COBOL modernization suite.

### Components
- Parser (from B2)
- Analyzer
- Java generator (from B3)
- C# generator (B4)
- Test generator
- Documentation generator

### Effort Estimate: 6 weken (incremental on B2, B3)

---

## B4: COBOL → C# Generator
**Categorie**: AI & Automatisering | **ROI**: 4.0 | **Bron**: Legacy-Mod-Agents

### Beschrijving
COBOL naar C#/.NET conversie.

### Effort Estimate: 5 weken

---

## B5: Multi-Agent Orchestration
**Categorie**: AI & Automatisering | **ROI**: 4.0 | **Bron**: Legacy-Mod-Agents

### Beschrijving
Meerdere AI agents samenwerken aan migratie tasks.

### Agent Types
- Analyzer Agent (code analysis)
- Generator Agent (code generation)
- Tester Agent (test creation)
- Reviewer Agent (quality check)
- Documenter Agent (documentation)

### Effort Estimate: 4 weken

---

## C2: RPG/AS400 Support
**Categorie**: Taal Support | **ROI**: 3.5 | **Bron**: awesome-legacy

### Beschrijving
IBM AS/400 RPG code analyse.

### Effort Estimate: 5 weken

---

## C5: PowerBuilder Support
**Categorie**: Taal Support | **ROI**: 3.0 | **Bron**: awesome-legacy

### Beschrijving
Sybase/SAP PowerBuilder analyse.

### Effort Estimate: 4 weken

---

## C6: Delphi/Object Pascal
**Categorie**: Taal Support | **ROI**: 4.0 | **Bron**: awesome-legacy

### Beschrijving
Delphi/Object Pascal code analyse.

### Effort Estimate: 3 weken

---

## I6: Containerization Wizard
**Categorie**: Cloud & Infra | **ROI**: 4.0 | **Bron**: XTi

### Beschrijving
Docker image generator voor legacy apps.

### Effort Estimate: 3 weken

---

## G4: Event Sourcing Bridge
**Categorie**: Migratie Patterns | **ROI**: 3.0 | **Bron**: LinkIT

### Beschrijving
Event-driven migratie pattern.

### Effort Estimate: 4 weken

---

## K5: Penetration Test Templates
**Categorie**: Security | **ROI**: 4.0 | **Bron**: awesome-legacy

### Beschrijving
Security test scripts voor legacy en nieuwe systemen.

### Effort Estimate: 3 weken

---

## Fase 6 Totaal Overzicht

| ID | Item | Weken | Dependencies |
|----|------|-------|--------------|
| C1 | COBOL Suite | 6 | B2, B3, B4 |
| B4 | COBOL → C# | 5 | B2 |
| B5 | Multi-Agent | 4 | B1, B6 |
| C2 | RPG/AS400 | 5 | - |
| C5 | PowerBuilder | 4 | - |
| C6 | Delphi | 3 | - |
| I6 | Container Wizard | 3 | - |
| G4 | Event Sourcing | 4 | G5 |
| K5 | Pentest Templates | 3 | K1 |
| **TOTAAL** | | **37 weken werk** | |

> **Note**: Met parallel development (3 teams) is Fase 6 in 16 weken te realiseren.

---

# DOCUMENTATIE & TRAINING (Parallel Track)

Deze items worden parallel aan de andere fases ontwikkeld.

| ID | Item | Weken | Fase |
|----|------|-------|------|
| H1 | Knowledge Transfer Program | 3 | 2-3 |
| H5 | Case Study Library | 2 | 3-4 |
| H6 | Legacy Code Glossary | 1 | 1 |
| H7 | Architecture Kata's | 2 | 4-5 |
| A5 | ROI Dashboard | 4 | 3 |
| A6 | Stakeholder Alignment Module | 1 | 1 |

---

# UITGESLOTEN ITEMS

De volgende items zijn **niet** opgenomen in de roadmap:

| ID | Gap | ROI | Reden |
|----|-----|-----|-------|
| C3 | FORTRAN Support | 2.0 | Te niche markt in NL/EU |
| C7 | Natural/ADABAS | 2.0 | Extreem complex, zeer kleine markt |
| C8 | Progress 4GL | 2.0 | Beperkte vraag |
| I7 | Serverless Converter | 2.0 | Markt nog niet klaar |
| H2 | Video Tutorial Platform | 2.5 | Outsourcen indien nodig |
| I3 | GCP Support | 2.5 | Azure/AWS prioriteit |

---

# TOTAAL OVERZICHT

## Resources & Timeline

| Fase | Weken Werk | Teams | Doorlooptijd | Start | Einde |
|------|------------|-------|--------------|-------|-------|
| 1 | 31 | 3 | 12 | Week 1 | Week 12 |
| 2 | 47 | 3 | 16 | Week 13 | Week 28 |
| 3 | 45 | 3 | 14 | Week 29 | Week 42 |
| 4 | 21 | 2 | 10 | Week 43 | Week 52 |
| 5 | 33 | 3 | 12 | Week 53 | Week 64 |
| 6 | 37 | 3 | 16 | Week 65 | Week 80 |
| **Totaal** | **214** | | **80 weken** | | |

## Investment Summary

| Metric | Value |
|--------|-------|
| Total Development Weeks | 224 (+10 nieuwe items) |
| Parallel Teams Needed | 2-3 |
| Calendar Duration | 82 weken (~19 maanden) |
| Items Delivered | 75 |
| Excluded Items | 6 |
| Nieuwe Items | 3 (B12, A7, H8) |

## Priority Distribution

| Priority Level | Items | % of Total |
|----------------|-------|------------|
| Critical (5) | 8 | 11% |
| High (4) | 28 | 39% |
| Medium (3) | 30 | 42% |
| Low (2) | 6 | 8% |

## Category Distribution

| Category | Items | Weken |
|----------|-------|-------|
| A: Assessment & Sales | 6 | 17 |
| B: AI & Automatisering | 11 | 41 |
| C: Taal Support | 4 | 18 |
| D: Target Platforms | 8 | 27 |
| E: Architecture | 6 | 19 |
| F: Testing | 8 | 19 |
| G: Migratie Patterns | 8 | 25 |
| H: Documentatie | 6 | 11 |
| I: Cloud & Infra | 5 | 17 |
| J: Monitoring | 6 | 18 |
| K: Security | 6 | 15 |

---

# AANBEVELINGEN & VERBETERINGEN

## Toegevoegde Items

### 1. **LLM Agent Collaboration Framework** (Nieuw - B12)
- Meerdere LLM agents werken samen aan analyse/migratie
- Agents kunnen elkaar consulteren en valideren
- Human-in-the-loop ALLEEN voor review en escalaties
- Geen real-time human collaboration (agents doen het werk)
- **ROI**: 4.5 | **Effort**: 4 weken | **Fase**: 3

### 2. **Cost Anomaly Detection** (Nieuw - A7)
- AI-powered cost prediction
- Alert bij budget overschrijding
- Optimization suggestions
- **ROI**: 4.0 | **Effort**: 3 weken | **Fase**: 2

### 3. **Project Export Suite** (Nieuw - H8)
- CSV export voor spreadsheets
- Excel (.xlsx) export met formatting
- LibreOffice Calc (.ods) export
- OpenProject/LibrePlan XML export
- MS Project (.mpp) compatible export
- **ROI**: 4.5 | **Effort**: 3 weken | **Fase**: 1

## Design Principes (Bevestigd)

### 1. **Kleine, Gespecialiseerde Analyzers**
- COBOL Parser (B2), Java Generator (B3), C# Generator (B4) blijven APART
- Kwaliteit boven snelheid
- Elke analyzer doet één ding heel goed
- Makkelijker te testen, debuggen en verbeteren
- Geen shortcuts door samenvoegen

### 2. **Human-in-the-Loop Principe**
- Humans reviewen ALLEEN, doen geen real-time werk
- LLM agents doen alle analyse en generatie
- Escalatie naar human bij:
  - Conflicterende resultaten
  - Onzekere beslissingen (confidence < threshold)
  - Security-gerelateerde keuzes
  - Business rule interpretatie

### 3. **E1 + E2 Parallel Ontwikkelen** (niet samenvoegen)
Dependency Map en Circular Detector delen infrastructuur maar zijn aparte tools.

### 4. **F2 + F3 + F4 als Testing Toolkit Package**
Alle Sprout/Wrap patterns in één coherent testing toolkit, maar intern als aparte modules.

### 5. **Quick Win Parallel Track**
Items < 2 weken kunnen parallel aan grotere items door junior devs.

---

# APPENDIX A: DEPENDENCY GRAPH

```
A1 (Quickscan)
├── A2 (Pricing)
├── A3 (TCO)
└── A4 (Strategy)

B9 (Field Mapper)
├── B8 (Headless)
│   ├── B10 (Dual Mode)
│   ├── B1 (AI Access)
│   │   └── B7 (NL Query)
│   └── B11 (AI Form Filler)
└── B2 (COBOL Parser)
    ├── B3 (→ Java)
    └── B4 (→ C#)
        └── C1 (Full COBOL Suite)

E1 (Dep Map)
├── E2 (Circular)
├── E4 (Lineage)
└── E5 (Impact)

F1 (Seam Model)
├── F2 (Sprout Method)
├── F3 (Sprout Class)
└── F4 (Wrap Method)

G1 (Adapters)
├── G2 (Side-by-Side)
└── G8 (ACL)

J2 (Baseline)
├── J6 (Health Check)
└── J1 (Dual Monitor)
    └── J5 (Rollback)

K3 (Secrets)
└── K1 (Vuln Scanner)
    └── K4 (Sec Debt)
        └── K2 (Compliance)
            └── K6 (Audit Trail)
```

---

# APPENDIX B: RISK REGISTER

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI model changes (Claude API) | High | Medium | Abstract LLM layer, multi-provider support |
| Low-code platform API changes | Medium | High | Version pinning, adapter pattern |
| Team scaling challenges | High | Medium | Documentation, knowledge transfer |
| Legacy system access restrictions | High | Low | Client-side deployment options |
| Regulatory changes (AI Act) | Medium | Medium | Compliance monitoring, audit trails |

---

# DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Week 144 | Claude + User | Initial complete roadmap |

---

*End of Document*
