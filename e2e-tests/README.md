# E2E Tests - MarQed AI Agent SD Platform

End-to-end test cases voor het platform. Deze tests valideren complete user flows.

## Directory Structuur

```
e2e-tests/
├── README.md                    # Dit bestand
├── screenshots/                 # Test screenshots (per testcase)
├── onboarding/                  # Project onboarding tests
│   ├── TC001_project_intake.md  # Testcase documentatie
│   └── screenshots/             # Screenshots voor deze test
├── workflows/                   # Workflow tests
├── agents/                      # Agent tests
└── quality/                     # Quality gate tests
```

## Test Case Format

Elke testcase heeft:
1. **ID**: TC[NNN]_[naam]
2. **Beschrijving**: Wat wordt getest
3. **Precondities**: Wat moet aanwezig zijn
4. **Stappen**: Gedetailleerde test stappen
5. **Verwacht resultaat**: Wat moet er gebeuren
6. **Screenshots**: Visuele verificatie

## Test Categories

| Category | Prefix | Beschrijving |
|----------|--------|--------------|
| Onboarding | TC001-TC099 | Project registratie & intake |
| Workflows | TC100-TC199 | Agent workflows |
| Quality | TC200-TC299 | Quality gates & validation |
| Agents | TC300-TC399 | Agent behavior |
| API | TC400-TC499 | API endpoint tests |

## Uitvoeren

Tests kunnen worden uitgevoerd met Playwright via Claude Code:
1. Start de backend: `uvicorn app.main:app --reload`
2. Gebruik Playwright MCP tools om tests uit te voeren
3. Screenshots worden opgeslagen in de betreffende test directory

## Status

| Test ID | Naam | Status | Laatste Run |
|---------|------|--------|-------------|
| TC001 | Project Intake | In Progress | 2025-11-27 |
