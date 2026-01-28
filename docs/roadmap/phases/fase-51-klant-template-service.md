# Fase 51: Klant Template Service - Multi-Tenant AI Coding Platform

**Status:** PLANNED
**Priority:** HIGH (ROI 8.0)
**Effort:** 312 uur (~10 weken)
**Timeline:** Week 191-200 (na Fase 32 Ralph Wiggum)
**Dependencies:** Fase 32 (Ralph Wiggum), Fase 23.5 (Confucius Orchestrator)

---

## 1. Executive Summary

De Klant Template Service transformeert MarQed.ai van een single-project platform naar een **multi-tenant AI coding platform** met:

- **Per-klant domeinen** met eigen configuratie en context
- **Per-applicatie omgevingen** met tech-stack specifieke tooling
- **Context inheritance** (Platform → Klant → Applicatie → Project)
- **Geautomatiseerde onboarding** via templates
- **VibeCoding workflow templates** voor professionele documentatie output

### Business Value

| Metric | Current | Target | Impact |
|--------|---------|--------|--------|
| Klant onboarding tijd | 2-4 uur handmatig | < 15 min geautomatiseerd | 90% reductie |
| Context relevantie | Generiek | Klant+app specifiek | 40% betere LLM output |
| Scanner configuratie | Handmatig | Auto per tech-stack | 100% consistent |
| Documentatie kwaliteit | Variabel | VibeCoding templates | Professioneel standaard |

---

## 2. Architecture Overview

### 2.1 Directory Structuur

```
/opt/marqed/
├── templates/                          # MASTER TEMPLATES
│   ├── klant-template/                 # Template voor nieuwe klant
│   │   ├── .claude/
│   │   │   ├── context/
│   │   │   │   ├── klant-profiel.md    # Placeholder template
│   │   │   │   ├── tech-preferences.md
│   │   │   │   └── business-domain.md
│   │   │   ├── agents/
│   │   │   │   └── klant-specialist.md # Klant-specifieke agent config
│   │   │   └── settings.local.json
│   │   ├── docs/
│   │   │   └── onboarding/
│   │   └── .mcp.json.template
│   │
│   ├── applicatie-templates/           # Per tech-stack templates
│   │   ├── python-app/
│   │   │   ├── .claude/
│   │   │   │   ├── context/
│   │   │   │   │   ├── tech-stack.md
│   │   │   │   │   └── tools.md
│   │   │   │   └── agents/
│   │   │   ├── scanners/
│   │   │   │   ├── bandit.json
│   │   │   │   ├── coverage-py.json
│   │   │   │   └── mypy.json
│   │   │   └── docs/
│   │   │       └── VibeCoding_Workflow_Templates/
│   │   │
│   │   ├── dotnet-app/
│   │   │   ├── .claude/context/
│   │   │   ├── scanners/
│   │   │   │   ├── asp-scanner.json
│   │   │   │   ├── dotnet-analyzer.json
│   │   │   │   └── roslyn.json
│   │   │   └── docs/VibeCoding_Workflow_Templates/
│   │   │
│   │   ├── legacy-asp/                 # Voor HCI-CRS type projecten
│   │   │   ├── .claude/context/
│   │   │   │   ├── tech-stack.md       # Classic ASP + VBScript
│   │   │   │   └── migration-notes.md
│   │   │   └── scanners/
│   │   │       ├── vbscript-analyzer.json
│   │   │       ├── stored-procedure-analyzer.json
│   │   │       └── classic-asp-detector.json
│   │   │
│   │   ├── javascript-app/
│   │   ├── typescript-app/
│   │   ├── go-app/
│   │   ├── java-app/
│   │   ├── php-legacy/
│   │   └── php-modern/
│   │
│   └── project-template/               # Sprint/project template
│       ├── .claude/context/
│       └── docs/sprint/
│
├── klanten/                            # KLANT DOMEINEN
│   └── [klant-slug]/
│       ├── .claude/                    # Klant-brede configuratie
│       │   ├── context/
│       │   │   ├── klant-profiel.md
│       │   │   ├── tech-preferences.md
│       │   │   └── business-domain.md
│       │   └── agents/
│       ├── applicaties/
│       │   └── [app-slug]/
│       │       ├── .claude/            # App-specifieke config
│       │       ├── scanners/           # Actieve scanner configs
│       │       ├── src/                # Symlink naar /opt/projecten/...
│       │       └── docs/
│       └── docs/                       # Klant-brede docs
│
└── projecten/                          # → /opt/projecten (bestaand)
```

### 2.2 Context Inheritance Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: PLATFORM CONTEXT (Globaal)                                     │
│  ├── MarQed capabilities, 11 agents, 15 workflows                        │
│  ├── Standaard kwaliteitseisen, security policies                        │
│  └── Inherited by: ALL                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: KLANT CONTEXT (Per klant)                                      │
│  ├── Klantprofiel, SLA niveau, contactpersonen                          │
│  ├── Tech preferences, coding standards, Git workflow                    │
│  ├── Business domain kennis, terminologie                                │
│  └── Inherited by: All apps + projects van deze klant                   │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 3: APPLICATIE CONTEXT (Per app)                                   │
│  ├── Tech stack (Python/Django, .NET/Blazor, etc.)                      │
│  ├── Architecture decisions, API specs                                   │
│  ├── Business rules, integrations                                        │
│  ├── Active scanners en analyzers                                        │
│  └── Inherited by: All projects van deze applicatie                     │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 4: PROJECT CONTEXT (Per sprint/project)                           │
│  ├── Sprint goals, current focus                                         │
│  ├── Active user stories, constraints                                    │
│  └── Temporary overrides                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 51A: Foundation & Templates (Week 191-193)

**Effort:** 80 uur (~3 weken)
**Focus:** Template structuur, basis services

| Component | Type | Description | Effort |
|-----------|------|-------------|--------|
| `KlantTemplateService` | Service | Template instantiation, placeholder replacement | 24h |
| `ApplicatieTemplateService` | Service | Tech-stack template selection, scanner config | 24h |
| `ContextInheritanceService` | Service | Merge platform→klant→app→project context | 16h |
| Template files | Templates | klant-template/, 8 applicatie-templates | 16h |

**Deliverables:**
- [ ] Master templates in `/opt/marqed/templates/`
- [ ] KlantTemplateService met placeholder engine
- [ ] ApplicatieTemplateService met tech-stack detection
- [ ] ContextInheritanceService met 4-layer merging
- [ ] Unit tests (20+ tests)

### Phase 51B: Scanner Configuration (Week 194-195)

**Effort:** 56 uur (~2 weken)
**Focus:** Per-app scanner configuratie

| Component | Type | Description | Effort |
|-----------|------|-------------|--------|
| `ScannerConfigService` | Service | Load/merge scanner configs per app | 20h |
| `ScannerRegistryService` | Service | Registry van alle 34+ scanners | 12h |
| Scanner config files | JSON | Per-stack scanner presets | 16h |
| Integration | Update | SecurityScanOrchestrator context-aware | 8h |

**Scanner Presets per Stack:**

| Stack | Scanners | Priority |
|-------|----------|----------|
| **Python** | bandit, coverage.py, mypy, safety | Standard |
| **.NET Modern** | asp-scanner, dotnet-analyzer, roslyn | Standard |
| **Legacy ASP** | vbscript-analyzer, sp-analyzer, classic-asp-detector, asp-scanner | Extended |
| **JavaScript** | eslint-security, npm-audit, snyk | Standard |
| **TypeScript** | tsc-strict, eslint-security, npm-audit | Standard |
| **Go** | gosec, staticcheck, govulncheck | Standard |
| **Java** | spotbugs, owasp-dependency-check, pmd | Standard |
| **PHP Legacy** | php-analyzer, phpstan (basic) | Standard |
| **PHP Modern** | php-modern-analyzer, phpstan, psalm | Extended |

**Deliverables:**
- [ ] ScannerConfigService met stack-aware loading
- [ ] ScannerRegistryService met alle 34+ scanners
- [ ] 8 scanner preset configuraties (JSON)
- [ ] SecurityScanOrchestrator update voor context
- [ ] Unit tests (15+ tests)

### Phase 51C: Onboarding Workflows (Week 196-197)

**Effort:** 64 uur (~2 weken)
**Focus:** Geautomatiseerde onboarding API en workflows

| Component | Type | Description | Effort |
|-----------|------|-------------|--------|
| `KlantOnboardingService` | Service | Klant domein provisioning orchestration | 20h |
| `ApplicatieOnboardingService` | Service | App omgeving provisioning | 20h |
| API Endpoints | Routes | /api/v2/klanten/*, /api/v2/applicaties/* | 16h |
| Database models | Models | KlantDomein, ApplicatieOmgeving, ContextDocument | 8h |

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/klanten/onboard` | POST | Start klant onboarding |
| `/api/v2/klanten/{id}` | GET | Get klant details |
| `/api/v2/klanten/{id}/applicaties/onboard` | POST | Start app onboarding |
| `/api/v2/klanten/{id}/applicaties/{app_id}` | GET | Get app details |
| `/api/v2/klanten/{id}/applicaties/{app_id}/context` | GET | Get merged context |
| `/api/v2/klanten/{id}/applicaties/{app_id}/scanners` | GET | Get active scanners |
| `/api/v2/klanten/{id}/applicaties/{app_id}/activate` | POST | Activate for session |

**Database Schema:**

```sql
-- Klant domein
CREATE TABLE klant_domeinen (
    id SERIAL PRIMARY KEY,
    klant_naam VARCHAR(255) NOT NULL,
    klant_slug VARCHAR(100) UNIQUE NOT NULL,
    domein_path VARCHAR(500) NOT NULL,
    sla_niveau VARCHAR(50) DEFAULT 'standard',
    branche VARCHAR(100),
    tech_preferences JSONB DEFAULT '{}',
    contacten JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Applicatie omgeving
CREATE TABLE applicatie_omgevingen (
    id SERIAL PRIMARY KEY,
    klant_id INTEGER REFERENCES klant_domeinen(id) ON DELETE CASCADE,
    app_naam VARCHAR(255) NOT NULL,
    app_slug VARCHAR(100) NOT NULL,
    app_type VARCHAR(50) NOT NULL, -- web, api, legacy, mobile
    tech_stack VARCHAR(50) NOT NULL, -- python, dotnet, legacy-asp, etc.
    omgeving_path VARCHAR(500) NOT NULL,
    source_path VARCHAR(500), -- /opt/projecten/...
    scanner_config JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(klant_id, app_slug)
);

-- Context documents (voor custom context)
CREATE TABLE context_documenten (
    id SERIAL PRIMARY KEY,
    applicatie_id INTEGER REFERENCES applicatie_omgevingen(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL, -- tech-stack, business-rules, known-issues
    document_path VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64), -- voor change detection
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Onboarding history
CREATE TABLE onboarding_history (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- klant, applicatie
    entity_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT NOW()
);
```

**Deliverables:**
- [ ] KlantOnboardingService met workflow orchestration
- [ ] ApplicatieOnboardingService met tech detection
- [ ] 7 API endpoints
- [ ] 4 database models + migration
- [ ] Unit tests (25+ tests)

### Phase 51D: VibeCoding Integration (Week 198-199)

**Effort:** 48 uur (~1.5 weken)
**Focus:** VibeCoding templates als documentatie output

| Component | Type | Description | Effort |
|-----------|------|-------------|--------|
| VibeCoding templates | Templates | 6 templates geadopteerd en aangepast | 16h |
| `DocumentGeneratorService` | Service | Generate docs van agent output | 20h |
| Agent integration | Update | Diana, Felix, Quinn output naar templates | 12h |

**Geadopteerde VibeCoding Templates:**

| Template | MarQed Agent | Output |
|----------|--------------|--------|
| `01_project_brief_and_prd.md` | Peter (GREEN_PAPER) | Project requirements document |
| `03_architecture_and_design.md` | Felix | Architecture decision records |
| `04_api_design_specification.md` | Felix | OpenAPI-style API specs |
| `06_security_and_readiness_checklists.md` | Quinn | Security audit reports |
| `09_deployment_and_operations.md` | Derek (NEW) | Deployment runbooks |
| `10_documentation_and_maintenance.md` | Diana | Technical documentation |

**Deliverables:**
- [ ] 6 aangepaste VibeCoding templates
- [ ] DocumentGeneratorService
- [ ] Agent output mapping naar templates
- [ ] Integration tests (10+ tests)

### Phase 51E: New Agents & Workflow (Week 200)

**Effort:** 64 uur (~2 weken)
**Focus:** Derek (DevOps) agent en DEPLOYMENT workflow

| Component | Type | Description | Effort |
|-----------|------|-------------|--------|
| `DerekAgent` | Agent | DevOps/Deployment specialist | 24h |
| `IsaacAgent` | Agent | Infrastructure Auditor | 16h |
| DEPLOYMENT workflow | Workflow | 6-phase deployment pipeline | 16h |
| Tests & docs | QA | E2E tests, documentation | 8h |

**Derek Agent Specification:**

```python
@dataclass
class DerekAgentConfig:
    """DevOps & Deployment Specialist"""
    name: str = "Derek"
    role: str = "DevOps Engineer"
    dev_model: str = "qwen2.5-coder:7b"
    prod_model: str = "qwen3-coder:32b"

    specialties: List[str] = field(default_factory=lambda: [
        "CI/CD pipeline design (GitHub Actions, GitLab CI, Azure DevOps)",
        "Container orchestration (Docker, Kubernetes, Docker Compose)",
        "Infrastructure as Code (Terraform, Pulumi, Ansible)",
        "Cloud deployment (AWS, Azure, GCP)",
        "Release management (Blue/Green, Canary, Rolling)",
        "Environment configuration (secrets, configs, feature flags)",
        "Monitoring setup (Prometheus, Grafana, alerts)"
    ])

    workflows: List[str] = field(default_factory=lambda: [
        "DEPLOYMENT",
        "INFRASTRUCTURE_AUDIT",
        "MIGRATION_ENHANCED"  # Phase 7
    ])

    tools: List[str] = field(default_factory=lambda: [
        "docker", "kubectl", "terraform", "ansible",
        "gh", "az", "aws", "gcloud"
    ])
```

**DEPLOYMENT Workflow:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT WORKFLOW                                                     │
│  Primary: Derek | Supporting: Isaac, Quinn, Tessa                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: PRE-DEPLOYMENT CHECK (Quinn + Isaac)                          │
│  ├── Security scan final (CWE scanners)                                 │
│  ├── Infrastructure audit (IaC review)                                  │
│  ├── Dependency vulnerability check                                     │
│  └── Gate: All critical issues resolved                                 │
│                                                                          │
│  Phase 2: BUILD & PACKAGE (Derek)                                       │
│  ├── Docker/container build                                             │
│  ├── Artifact creation and signing                                      │
│  ├── Version tagging (semantic versioning)                              │
│  └── Push to registry                                                   │
│                                                                          │
│  Phase 3: STAGING DEPLOYMENT (Derek)                                    │
│  ├── Deploy to staging environment                                      │
│  ├── Database migrations (if applicable)                                │
│  ├── Configuration validation                                           │
│  └── Smoke tests execution                                              │
│                                                                          │
│  Phase 4: VALIDATION (Tessa + Quinn)                                    │
│  ├── E2E test suite execution                                           │
│  ├── Performance baseline comparison                                    │
│  ├── Security validation (OWASP checks)                                 │
│  └── Gate: 95%+ tests passing, no regressions                          │
│                                                                          │
│  Phase 5: PRODUCTION DEPLOYMENT (Derek)                                 │
│  ├── Deployment strategy execution (Blue/Green, Canary)                 │
│  ├── Health check validation                                            │
│  ├── Traffic shifting (gradual rollout)                                 │
│  └── Rollback plan activated                                            │
│                                                                          │
│  Phase 6: POST-DEPLOYMENT (Derek + Diana)                               │
│  ├── Monitoring dashboard verification                                  │
│  ├── Alert configuration check                                          │
│  ├── Release notes generation                                           │
│  └── Stakeholder notification                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Deliverables:**
- [ ] DerekAgent implementation
- [ ] IsaacAgent implementation
- [ ] DEPLOYMENT workflow (6 phases)
- [ ] Agent tests (15+ tests)
- [ ] Workflow E2E tests (10+ tests)

---

## 4. Detailed Time Estimation

### 4.1 Phase Breakdown

| Phase | Focus | Effort | Calendar |
|-------|-------|--------|----------|
| **51A** | Foundation & Templates | 80h | 3 weken |
| **51B** | Scanner Configuration | 56h | 2 weken |
| **51C** | Onboarding Workflows | 64h | 2 weken |
| **51D** | VibeCoding Integration | 48h | 1.5 weken |
| **51E** | New Agents & Workflow | 64h | 2 weken |
| **TOTAAL** | | **312h** | **~10 weken** |

### 4.2 Detailed Task Breakdown

#### Phase 51A: Foundation & Templates (80h)

| Task | Effort | Complexity | Dependencies |
|------|--------|------------|--------------|
| Design template directory structure | 4h | Medium | - |
| Create klant-template base files | 8h | Low | Structure |
| Create 8 applicatie-template directories | 16h | Medium | Structure |
| Implement KlantTemplateService | 16h | Medium | Templates |
| Implement ApplicatieTemplateService | 16h | Medium | Templates |
| Implement ContextInheritanceService | 12h | High | Services |
| Unit tests | 8h | Medium | All services |

#### Phase 51B: Scanner Configuration (56h)

| Task | Effort | Complexity | Dependencies |
|------|--------|------------|--------------|
| Design scanner registry schema | 4h | Medium | - |
| Create scanner preset JSONs (8 stacks) | 12h | Low | Schema |
| Implement ScannerRegistryService | 8h | Medium | Presets |
| Implement ScannerConfigService | 12h | Medium | Registry |
| Update SecurityScanOrchestrator | 8h | High | ConfigService |
| Integration with existing scanners | 8h | Medium | Orchestrator |
| Unit tests | 4h | Medium | All |

#### Phase 51C: Onboarding Workflows (64h)

| Task | Effort | Complexity | Dependencies |
|------|--------|------------|--------------|
| Database schema design | 4h | Medium | - |
| Alembic migration | 4h | Low | Schema |
| SQLAlchemy models | 8h | Medium | Migration |
| Implement KlantOnboardingService | 16h | High | Models, 51A |
| Implement ApplicatieOnboardingService | 12h | High | Models, 51A |
| API endpoints (7) | 12h | Medium | Services |
| Unit tests | 8h | Medium | All |

#### Phase 51D: VibeCoding Integration (48h)

| Task | Effort | Complexity | Dependencies |
|------|--------|------------|--------------|
| Adapt VibeCoding templates (6) | 12h | Low | - |
| Implement DocumentGeneratorService | 16h | Medium | Templates |
| Integrate with Diana agent | 8h | Medium | Generator |
| Integrate with Felix agent | 6h | Medium | Generator |
| Integrate with Quinn agent | 6h | Medium | Generator |

#### Phase 51E: New Agents & Workflow (64h)

| Task | Effort | Complexity | Dependencies |
|------|--------|------------|--------------|
| DerekAgent implementation | 16h | High | Agent framework |
| DerekAgent prompt engineering | 8h | Medium | Agent |
| IsaacAgent implementation | 12h | Medium | Agent framework |
| DEPLOYMENT workflow design | 8h | High | Derek, Isaac |
| DEPLOYMENT workflow implementation | 12h | High | Design |
| E2E tests | 8h | Medium | Workflow |

### 4.3 Risk Factors

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Template complexity underestimated | +20% effort | Medium | Start with MVP templates |
| Scanner integration issues | +10% effort | Low | Existing scanner infrastructure |
| Context inheritance edge cases | +15% effort | Medium | Extensive testing |
| New agent quality | +10% effort | Low | Follow existing agent patterns |

**Adjusted Estimate with Risk Buffer:** 312h + 15% = **~360h (~11-12 weken)**

---

## 5. Success Criteria

### 5.1 Functional Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Klant onboarding time | < 15 min | End-to-end timing |
| Applicatie onboarding time | < 10 min | End-to-end timing |
| Context inheritance accuracy | 100% | All 4 layers merged correctly |
| Scanner auto-configuration | 100% | All stacks have presets |
| VibeCoding template coverage | 6 templates | Agent output mapping |

### 5.2 Technical Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test coverage | > 80% | pytest-cov |
| API response time | < 2s | Onboarding endpoints |
| Template instantiation | < 5s | Placeholder replacement |
| Context merge time | < 1s | 4-layer merge |

### 5.3 Quality Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Unit tests passing | 100% | CI/CD |
| Integration tests passing | 95%+ | CI/CD |
| Documentation complete | 100% | All services documented |
| No critical security issues | 0 | Security scan |

---

## 6. Dependencies

### 6.1 Prerequisites

| Dependency | Status | Required For |
|------------|--------|--------------|
| Fase 32: Ralph Wiggum | PLANNED (Week 175-190) | Unified state management patterns |
| Fase 23.5: Confucius Orchestrator | ✅ COMPLETE | Workflow orchestration |
| Existing 34+ scanners | ✅ COMPLETE | Scanner presets |
| Existing 11 agents | ✅ COMPLETE | Agent integration |

### 6.2 External Dependencies

| Dependency | Type | Required For |
|------------|------|--------------|
| `/opt/projecten/` directory | Infrastructure | Source code symlinks |
| `/opt/marqed/` directory | Infrastructure | Template & klant storage |
| Database (PostgreSQL) | Infrastructure | New tables |

---

## 7. API Reference (Preview)

### 7.1 Klant Onboarding

```http
POST /api/v2/klanten/onboard
Content-Type: application/json

{
    "klant_naam": "ACME Corporation",
    "branche": "healthcare",
    "sla_niveau": "professional",
    "contacten": [
        {
            "rol": "product_owner",
            "naam": "Jan Jansen",
            "email": "jan@acme.nl"
        }
    ],
    "tech_preferences": {
        "primary_stack": "dotnet",
        "git_workflow": "gitflow",
        "ci_cd": "azure_devops"
    }
}

Response:
{
    "klant_id": 1,
    "klant_slug": "acme-corporation",
    "domein_path": "/opt/marqed/klanten/acme-corporation",
    "status": "created",
    "next_steps": [
        "Onboard eerste applicatie via /api/v2/klanten/1/applicaties/onboard"
    ]
}
```

### 7.2 Applicatie Onboarding

```http
POST /api/v2/klanten/1/applicaties/onboard
Content-Type: application/json

{
    "app_naam": "Patient Portal",
    "app_type": "web",
    "tech_stack": "dotnet",
    "source_path": "/opt/projecten/acme/patient-portal",
    "description": "Web portal voor patiënt communicatie"
}

Response:
{
    "applicatie_id": 1,
    "app_slug": "patient-portal",
    "omgeving_path": "/opt/marqed/klanten/acme-corporation/applicaties/patient-portal",
    "active_scanners": [
        "asp-scanner",
        "dotnet-analyzer",
        "roslyn"
    ],
    "context_files": [
        ".claude/context/tech-stack.md",
        ".claude/context/tools.md"
    ],
    "status": "ready"
}
```

### 7.3 Get Merged Context

```http
GET /api/v2/klanten/1/applicaties/1/context

Response:
{
    "layers": {
        "platform": { ... },
        "klant": {
            "naam": "ACME Corporation",
            "sla": "professional",
            ...
        },
        "applicatie": {
            "naam": "Patient Portal",
            "tech_stack": "dotnet",
            ...
        },
        "project": null
    },
    "merged": {
        "full_context_markdown": "# Context voor Patient Portal\n\n## Klant: ACME Corporation\n..."
    }
}
```

---

## 8. File Structure (New Files)

```
backend/
├── app/
│   ├── api/
│   │   └── v2/
│   │       ├── klant_onboarding.py          # NEW
│   │       └── applicatie_onboarding.py     # NEW
│   ├── models/
│   │   ├── klant_domein.py                  # NEW
│   │   ├── applicatie_omgeving.py           # NEW
│   │   └── context_document.py              # NEW
│   └── services/
│       ├── klant_template_service.py        # NEW
│       ├── applicatie_template_service.py   # NEW
│       ├── context_inheritance_service.py   # NEW
│       ├── scanner_config_service.py        # NEW
│       ├── scanner_registry_service.py      # NEW
│       ├── klant_onboarding_service.py      # NEW
│       ├── applicatie_onboarding_service.py # NEW
│       ├── document_generator_service.py    # NEW
│       └── agents/
│           ├── derek_agent.py               # NEW
│           └── isaac_agent.py               # NEW
├── alembic/
│   └── versions/
│       └── xxx_klant_template_tables.py     # NEW migration
└── tests/
    └── services/
        └── fase51/
            ├── test_klant_template_service.py
            ├── test_applicatie_template_service.py
            ├── test_context_inheritance_service.py
            ├── test_scanner_config_service.py
            ├── test_onboarding_services.py
            └── test_deployment_workflow.py

/opt/marqed/                                  # NEW directory structure
├── templates/
│   ├── klant-template/
│   └── applicatie-templates/
│       ├── python-app/
│       ├── dotnet-app/
│       ├── legacy-asp/
│       └── ...
└── klanten/
    └── [created at runtime]
```

---

## 9. Related Documentation

| Document | Description |
|----------|-------------|
| [claude-agentic-coding-template analysis](docs/analysis/claude-agentic-template-analysis.md) | Source template analysis |
| [AGENTS.md](.project/AGENTS.md) | Agent specifications |
| [Fase 32 Ralph Wiggum](docs/roadmap/phases/fase-32-ralph-wiggum-loop.md) | Prerequisite fase |
| [Security Scanner Suite](docs/roadmap/phases/fase-31-cwe-security-scanners.md) | Scanner infrastructure |

---

## 10. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-26 | 1.0 | Initial specification |

