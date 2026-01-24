# MarQed Platform: E2E Testing Strategy Advies

**Auteur:** Claude Code Analysis
**Datum:** 2026-01-22
**Scope:** End-to-end testing framework selectie en implementatiestrategie

---

## Executive Summary

Na analyse van het MarQed platform (Python backend, 40+ HTML dashboards, 2,700+ unit tests) en vergelijking van Shortest en agent-browser, adviseer ik een **hybride aanpak**:

| Layer | Tool | Reden |
|-------|------|-------|
| **Unit/Integration** | pytest (behouden) | 2,700+ tests, mature, stabiel |
| **API E2E** | pytest + httpx | Consistentie met bestaande codebase |
| **UI E2E - Regression** | Playwright (direct) | Deterministic, snelle feedback |
| **UI E2E - Exploratory** | agent-browser | AI agent testing, edge cases |
| **UI E2E - Acceptance** | Shortest | Stakeholder-leesbare tests |

**Aanbeveling:** Start met **Playwright** voor core regression, voeg **agent-browser** toe voor AI-driven exploratory testing, en gebruik **Shortest** voor high-level acceptance tests die stakeholders kunnen lezen.

---

## 1. Platform Analyse

### 1.1 MarQed Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (40+ dashboards)                │
│  project-intake.html | brown-paper-dashboard.html | ...     │
│  Vanilla JS + Fetch API + D3.js visualizations              │
├─────────────────────────────────────────────────────────────┤
│                    BACKEND (FastAPI Python)                 │
│  /api/* endpoints | Async services | SQLAlchemy ORM         │
│  2,700+ pytest tests | 97.8% pass rate                      │
├─────────────────────────────────────────────────────────────┤
│                    AI ORCHESTRATION                         │
│  Confucius (4 orchestrators) | Ralph Wiggum (autonomous)    │
│  LLM Council | Multi-model support (Anthropic/Ollama)       │
├─────────────────────────────────────────────────────────────┤
│                    DATA LAYER                               │
│  PostgreSQL | Redis | Filesystem (project analysis)         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Huidige Test Status

| Categorie | Status | Tooling |
|-----------|--------|---------|
| Unit Tests | 2,700+ tests, 97.8% pass | pytest |
| Integration Tests | Aanwezig | pytest + fixtures |
| API Tests | Aanwezig | pytest + httpx |
| E2E Tests | Handmatig met Playwright MCP | Markdown testcases |

### 1.3 Test Requirements voor MarQed

| Requirement | Prioriteit | Uitdaging |
|-------------|------------|-----------|
| **Workflow validation** | CRITICAL | Multi-step flows (Brown Paper 6 stages) |
| **LLM response testing** | HIGH | Non-deterministic AI output |
| **Dashboard interactie** | HIGH | 40+ dashboards, D3.js charts |
| **Long-running processes** | MEDIUM | Async workflows, SSE streaming |
| **Security testing** | MEDIUM | XSS, injection in formulieren |
| **Cross-browser** | LOW | Primary users = developers |

---

## 2. Framework Vergelijking voor MarQed

### 2.1 Scoring Matrix

| Criterium | Gewicht | Shortest | agent-browser | Playwright | pytest |
|-----------|---------|----------|---------------|------------|--------|
| **MarQed Fit** | 25% | 6 | 8 | 9 | 10 |
| **Bestaande integratie** | 20% | 3 | 5 | 7 | 10 |
| **AI workflow testing** | 20% | 8 | 9 | 5 | 4 |
| **Determinism** | 15% | 4 | 5 | 10 | 10 |
| **Onderhoudbaarheid** | 10% | 6 | 7 | 9 | 9 |
| **Stakeholder readability** | 10% | 10 | 5 | 6 | 3 |
| **Gewogen Score** | 100% | **5.85** | **6.75** | **7.65** | **8.0** |

### 2.2 Gedetailleerde Analyse per Framework

#### Shortest

**Sterktes voor MarQed:**
- Stakeholders (management) kunnen tests lezen
- AI-powered interpretatie past bij MarQed's AI focus
- Natural language tests documenteren workflows

**Zwaktes voor MarQed:**
- Python backend → TypeScript tests = context switch
- Non-deterministic (AI interpreteert anders)
- Claude API kosten per test run
- Geen pytest integratie

**Beste gebruik:** Acceptance tests voor belangrijke user journeys die stakeholders moeten begrijpen.

```typescript
// Voorbeeld: MarQed Brown Paper workflow test
shortest("Brown Paper analyse van HCI-CRS", {
  projectPath: "/opt/projecten/hci-crs",
  projectName: "HCI-CRS"
})
  .expect("Open Brown Paper dashboard")
  .expect("Start nieuwe analyse sessie")
  .expect("Beantwoord de 8 intake vragen")
  .expect("Controleer dat dependency graph wordt getoond")
  .expect("Controleer dat tech debt rapport is gegenereerd");
```

#### agent-browser

**Sterktes voor MarQed:**
- Perfect voor AI agent testing (Ralph Wiggum, Confucius)
- 93% context reductie → goedkoper dan Shortest
- Model-agnostisch (Anthropic, OpenAI, Ollama)
- Zero-config, direct bruikbaar

**Zwaktes voor MarQed:**
- Geen ingebouwde test framework
- Vereist wrapper voor assertions
- Shell-based → minder type safety

**Beste gebruik:** Exploratory testing door AI agents, edge case detectie, Ralph Wiggum integration.

```bash
# Voorbeeld: AI agent test voor project intake
agent-browser open "http://localhost:8000/project-intake.html"
agent-browser snapshot -i
agent-browser fill @projectPath "/opt/projecten/hci-crs"
agent-browser fill @projectName "HCI-CRS"
agent-browser click @startIntake
# AI agent analyseert resultaat en rapporteert issues
```

#### Playwright (Direct)

**Sterktes voor MarQed:**
- Deterministic tests → betrouwbare CI/CD
- Python API beschikbaar (playwright-python)
- Beste integratie met bestaande pytest setup
- Snelste feedback loop

**Zwaktes voor MarQed:**
- Brittle selectors bij UI wijzigingen
- Meer code voor dezelfde coverage
- Niet AI-aware

**Beste gebruik:** Core regression tests voor kritieke workflows.

```python
# Voorbeeld: pytest-playwright integratie
import pytest
from playwright.sync_api import Page

def test_project_intake_flow(page: Page):
    page.goto("http://localhost:8000/project-intake.html")
    page.fill("#projectPath", "/opt/projecten/hci-crs")
    page.fill("#projectName", "HCI-CRS")
    page.click("#startIntake")
    page.wait_for_selector(".intake-complete")
    assert page.locator(".tech-stacks").count() > 0
```

---

## 3. Aanbevolen Strategie: Testing Pyramid voor MarQed

```
                    ┌───────────────┐
                    │   Shortest    │  ← Acceptance (5-10 tests)
                    │  Stakeholder  │     Leesbaar, business-kritiek
                    │    Tests      │
                    ├───────────────┤
                ┌───┴───────────────┴───┐
                │    agent-browser      │  ← Exploratory (AI-driven)
                │   AI Agent Testing    │     Edge cases, chaos
                │   Ralph Wiggum Loops  │
                ├───────────────────────┤
            ┌───┴───────────────────────┴───┐
            │        Playwright             │  ← E2E Regression (20-30 tests)
            │    UI Component Tests         │     Deterministic, CI/CD
            │    Critical Path Testing      │
            ├───────────────────────────────┤
        ┌───┴───────────────────────────────┴───┐
        │            pytest + httpx             │  ← API Integration (100+ tests)
        │          API Endpoint Tests           │     Fast, reliable
        │          Service Integration          │
        ├───────────────────────────────────────┤
    ┌───┴───────────────────────────────────────┴───┐
    │                  pytest                       │  ← Unit Tests (2,700+ tests)
    │              Unit Tests (behouden)            │     Foundation, fast
    └───────────────────────────────────────────────┘
```

---

## 4. Implementatie Roadmap

### Fase 1: Playwright Foundation (Week 1-2)

**Doel:** Deterministic regression suite voor kritieke workflows

**Deliverables:**
1. `pytest-playwright` integratie in bestaande test setup
2. Page Object Model voor 5 core dashboards
3. 15-20 regression tests

**Prioriteit Dashboards:**
| Dashboard | Tests | Kritiek |
|-----------|-------|---------|
| project-intake.html | 3 | Project registratie |
| brown-paper-dashboard.html | 5 | Core workflow |
| quality-dashboard.html | 3 | Quality gates |
| agent-dashboard.html | 3 | Agent monitoring |
| security-dashboard.html | 3 | Security findings |

**Code Structure:**
```
backend/tests/
├── e2e/
│   ├── conftest.py          # Playwright fixtures
│   ├── pages/               # Page Object Models
│   │   ├── __init__.py
│   │   ├── project_intake.py
│   │   ├── brown_paper.py
│   │   └── ...
│   ├── test_project_intake.py
│   ├── test_brown_paper_workflow.py
│   └── ...
```

### Fase 2: agent-browser Integration (Week 3-4)

**Doel:** AI-driven exploratory testing voor edge cases

**Deliverables:**
1. agent-browser wrapper library (TypeScript of Python)
2. Integration met Ralph Wiggum autonomous loop
3. 5-10 exploratory test scenarios

**Use Cases:**
- Ralph Wiggum gebruikt agent-browser voor autonomous UI testing
- Edge case detectie in formulieren
- Accessibility testing via AI interpretatie

**Code Structure:**
```
backend/tests/
├── exploratory/
│   ├── agent_browser_wrapper.py
│   ├── scenarios/
│   │   ├── chaos_intake.py       # Random input testing
│   │   ├── slow_network.py       # Network degradation
│   │   └── concurrent_users.py   # Multi-user scenarios
│   └── reports/
```

### Fase 3: Shortest Acceptance Tests (Week 5-6)

**Doel:** Stakeholder-leesbare acceptance tests

**Deliverables:**
1. Shortest setup in MarQed repo
2. 5-10 high-level acceptance tests
3. Integration met CI/CD (optional, scheduled)

**Test Candidates:**
| Test | Beschrijving |
|------|--------------|
| Complete Brown Paper Analyse | Van intake tot rapport |
| Security Scan Workflow | Detectie tot remediation |
| Project Quickscan | 15-min Go/No-Go assessment |
| Quality Gate Evaluation | Pass/Fail beslissing |
| Migration Planning | Van analyse tot planning |

**Code Structure:**
```
e2e-tests/
├── shortest/
│   ├── shortest.config.ts
│   ├── acceptance/
│   │   ├── brown-paper-complete.test.ts
│   │   ├── security-scan.test.ts
│   │   └── quickscan.test.ts
│   └── fixtures/
```

### Fase 4: CI/CD Integration (Week 7-8)

**Doel:** Automated testing in deployment pipeline

**Pipeline Design:**
```yaml
# .github/workflows/e2e-tests.yml
stages:
  unit-tests:        # pytest (altijd)
    - pytest backend/tests/unit/

  api-tests:         # pytest + httpx (altijd)
    - pytest backend/tests/api/

  e2e-playwright:    # Playwright (PR + main)
    - pytest backend/tests/e2e/ --headed=false

  e2e-shortest:      # Shortest (nightly, scheduled)
    - npx shortest e2e-tests/shortest/acceptance/

  exploratory:       # agent-browser (weekly, manual)
    - python backend/tests/exploratory/run_scenarios.py
```

---

## 5. ROI Analyse

### Kosten vs Baten

| Framework | Setup Kosten | Running Kosten | Baten |
|-----------|--------------|----------------|-------|
| **Playwright** | 16-24 uur | Gratis | Snelle, betrouwbare regression |
| **agent-browser** | 8-16 uur | Minimal API costs | AI-driven edge case detectie |
| **Shortest** | 8-16 uur | ~$0.10-0.50/test | Stakeholder buy-in, documentatie |

### Break-even Analyse

**Scenario: Bug in Brown Paper workflow**
- Zonder E2E: Gemiddeld 4 uur debugging + 2 uur fix = 6 uur
- Met Playwright: 15 min test failure + 2 uur fix = 2.25 uur
- **Besparing per bug:** 3.75 uur

**Bij 2 bugs/maand:** 7.5 uur/maand × 12 = **90 uur/jaar besparing**

---

## 6. Concrete Aanbevelingen

### Prioriteit 1: Nu Implementeren

1. **Installeer pytest-playwright**
   ```bash
   pip install pytest-playwright
   playwright install chromium
   ```

2. **Maak Page Object Model voor brown-paper-dashboard.html**
   - Meest gebruikte workflow
   - Hoogste business waarde

3. **Schrijf 5 Playwright tests voor Brown Paper**
   - Session start
   - Question answering
   - Analysis trigger
   - Results display
   - Export functionality

### Prioriteit 2: Korte Termijn (Week 3-4)

1. **Integreer agent-browser voor Ralph Wiggum**
   - Ralph kan UI valideren tijdens autonomous loops
   - Snapshot-based verification

2. **Exploratory test scenarios**
   - Random input fuzzing
   - Performance under load
   - Error recovery testing

### Prioriteit 3: Middellange Termijn (Week 5-8)

1. **Shortest voor acceptance tests**
   - 5 kritieke user journeys
   - Stakeholder review sessie

2. **CI/CD pipeline**
   - Playwright op elke PR
   - Shortest nightly
   - agent-browser weekly

---

## 7. Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| **LLM non-determinism in Shortest** | Tests falen random | Retry logic, threshold-based assertions |
| **UI wijzigingen breken tests** | Maintenance overhead | Page Object Model, data-testid attributes |
| **agent-browser tool instabiliteit** | Tests falen | Fallback naar Playwright voor kritieke tests |
| **Kosten bij veel Shortest tests** | Budget overschrijding | Rate limiting, scheduled runs |

---

## 8. Conclusie

Voor het MarQed platform adviseer ik een **gedifferentieerde teststrategie**:

| Test Type | Framework | Frequentie | Doel |
|-----------|-----------|------------|------|
| Regression | Playwright | Elke PR | Snelle, betrouwbare feedback |
| Exploratory | agent-browser | Wekelijks | Edge case detectie |
| Acceptance | Shortest | Nightly | Stakeholder validatie |

**Start met Playwright** voor de foundation, voeg **agent-browser** toe voor AI-driven testing (past perfect bij Ralph Wiggum en Confucius), en gebruik **Shortest** voor stakeholder-facing acceptance tests.

Deze combinatie levert:
- **Snelle feedback** (Playwright: <5 min)
- **Intelligente testing** (agent-browser: AI-driven)
- **Stakeholder alignment** (Shortest: leesbaar)
- **Kostenefficiënt** (Playwright gratis, agent-browser goedkoop)

---

## Bronnen

- [Playwright Python](https://playwright.dev/python/)
- [pytest-playwright](https://pytest-playwright.readthedocs.io/)
- [agent-browser npm](https://www.npmjs.com/package/agent-browser)
- [agent-browser GitHub](https://github.com/vercel-labs/agent-browser)
- [Shortest npm](https://www.npmjs.com/package/@antiwork/shortest)
- [Shortest GitHub](https://github.com/antiwork/shortest)

---

*Document gegenereerd: 2026-01-22*
