# Plan van Aanpak: E2E Playwright Demo

**Doel:** Live demo van Playwright E2E tests op maandag 11:00
**Periode:** Donderdag 22 jan - Zondag 25 jan 2026
**Demo datum:** Maandag 26 januari 2026, 11:00 uur

---

## Executive Summary

| Dag | Focus | Deliverables |
|-----|-------|--------------|
| **Donderdag** | Setup & Foundation | Playwright geïnstalleerd, 2 tests werkend |
| **Vrijdag** | Core Tests | Alle 8 testcases geconverteerd |
| **Zaterdag** | Demo UI & Polish | Mooi rapport, individuele test runs |
| **Zondag** | Dry Runs & Cleanup | 3x testrun, cleanup verificatie, dress rehearsal |
| **Maandag 11:00** | **DEMO** | Live demonstratie |

---

## Bestaande Testcases (te converteren)

| ID | Naam | Categorie | Prioriteit |
|----|------|-----------|------------|
| TC001 | Project Intake | Onboarding | HIGH |
| TC101 | Project Analysis HCI-CRS | Workflows | HIGH |
| TC102 | Migration Planning HCI-CRS | Workflows | MEDIUM |
| TC103 | Full Assessment HCI-CRS | Workflows | MEDIUM |
| TC201 | Ghostcrew Quick Scan | Workflows | LOW |
| TC202 | Ghostcrew Full Crew Scan | Workflows | LOW |
| TC203 | Ghostcrew Assist Mode | Workflows | LOW |
| TC204 | Ghostcrew Workflow Integration | Workflows | LOW |

**Demo focus:** TC001, TC101, TC102 (hoogste waarde voor stakeholders)

---

## Dag 1: Donderdag 22 januari - Setup & Foundation

### Ochtend (09:00 - 12:00)

#### 1.1 Playwright Installatie
```bash
# In backend directory
cd /home/eddie/Projects/MarkdownTaskManager/backend
pip install pytest-playwright playwright pytest-html pytest-xdist
playwright install chromium
playwright install-deps
```

#### 1.2 Project Structuur Opzetten
```
backend/tests/e2e/
├── conftest.py              # Pytest fixtures, browser setup
├── pytest.ini               # Playwright configuratie
├── pages/                   # Page Object Models
│   ├── __init__.py
│   ├── base_page.py         # Basis pagina class
│   ├── project_intake.py    # Project Intake POM
│   ├── brown_paper.py       # Brown Paper Dashboard POM
│   └── ghostcrew.py         # Ghostcrew Dashboard POM
├── tests/
│   ├── __init__.py
│   ├── test_tc001_project_intake.py
│   ├── test_tc101_project_analysis.py
│   ├── test_tc102_migration_planning.py
│   └── ...
├── fixtures/
│   ├── test_data.py         # Test data configuratie
│   └── cleanup.py           # Cleanup utilities
└── reports/                 # HTML rapporten output
```

#### 1.3 Basis Configuratie (conftest.py)
```python
import pytest
from playwright.sync_api import Page, Browser
from typing import Generator

# Test data die opgeruimd moet worden
TEST_DATA_REGISTRY = []

@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": {"width": 1920, "height": 1080},
        "locale": "nl-NL",
        "timezone_id": "Europe/Amsterdam",
    }

@pytest.fixture
def page(browser: Browser) -> Generator[Page, None, None]:
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session", autouse=True)
def cleanup_after_all_tests():
    """Cleanup na alle tests"""
    yield
    # Cleanup alle test data
    for cleanup_fn in TEST_DATA_REGISTRY:
        cleanup_fn()
```

### Middag (13:00 - 17:00)

#### 1.4 Eerste Test: TC001 Project Intake
- [ ] Page Object Model voor project-intake.html
- [ ] Test implementatie met assertions
- [ ] Screenshot capture op elke stap
- [ ] Cleanup functie voor test data

#### 1.5 Dry Run #1 (door Claude)
- [ ] Test lokaal uitvoeren
- [ ] Verify screenshots worden opgeslagen
- [ ] Verify cleanup werkt

### Avond (19:00 - 21:00)

#### 1.6 Tweede Test: TC101 Project Analysis
- [ ] Page Object Model voor brown-paper-dashboard.html
- [ ] Test implementatie
- [ ] Integratie met TC001 (dependency)

**Checkpoint Donderdag:** 2 tests werkend, structuur opgezet

---

## Dag 2: Vrijdag 23 januari - Core Tests

### Ochtend (09:00 - 12:00)

#### 2.1 TC102 Migration Planning
- [ ] Uitbreiden Brown Paper POM
- [ ] Migration flow testen
- [ ] SSE streaming handling (indien nodig)

#### 2.2 TC103 Full Assessment
- [ ] Combinatie van TC101 + TC102
- [ ] End-to-end workflow test

### Middag (13:00 - 17:00)

#### 2.3 Ghostcrew Tests (TC201-TC204)
- [ ] Ghostcrew Dashboard POM
- [ ] 4 Ghostcrew tests implementeren
- [ ] Parallelle test execution testen

#### 2.4 Dry Run #2 (door Claude)
- [ ] Alle 8 tests uitvoeren
- [ ] Identify flaky tests
- [ ] Fix issues

### Avond (19:00 - 21:00)

#### 2.5 Test Isolation
- [ ] Elke test individueel kunnen draaien
- [ ] Geen dependencies tussen tests (behalve waar expliciet)
- [ ] `pytest -k "test_tc001"` moet werken

**Checkpoint Vrijdag:** Alle 8 tests geconverteerd en werkend

---

## Dag 3: Zaterdag 24 januari - Demo UI & Polish

### Ochtend (09:00 - 12:00)

#### 3.1 HTML Test Report
```bash
# Genereer mooi HTML rapport
pytest backend/tests/e2e/ --html=reports/e2e-report.html --self-contained-html
```

- [ ] pytest-html configureren
- [ ] Custom styling voor rapport
- [ ] Screenshots inline in rapport

#### 3.2 Demo Dashboard (optioneel)
- [ ] Simpele HTML pagina die tests kan triggeren
- [ ] Live output streaming
- [ ] Test selectie UI

### Middag (13:00 - 17:00)

#### 3.3 Test Runner Scripts
```bash
# scripts/run-e2e-demo.sh
#!/bin/bash

echo "🎬 MarQed E2E Test Demo"
echo "========================"

# Selecteer test
case $1 in
  "tc001") pytest backend/tests/e2e/tests/test_tc001_project_intake.py -v --headed ;;
  "tc101") pytest backend/tests/e2e/tests/test_tc101_project_analysis.py -v --headed ;;
  "all")   pytest backend/tests/e2e/ -v --headed ;;
  *)       echo "Usage: $0 [tc001|tc101|tc102|tc103|tc201|tc202|tc203|tc204|all]" ;;
esac
```

#### 3.4 Headed Mode Testing
- [ ] `--headed` flag werkt voor live demo
- [ ] Browser venster positionering
- [ ] Slowmo voor zichtbaarheid: `--slowmo=500`

### Avond (19:00 - 21:00)

#### 3.5 Cleanup Mechanisme Finaliseren
```python
# fixtures/cleanup.py
class TestDataCleaner:
    def __init__(self):
        self.created_projects = []
        self.created_sessions = []

    def register_project(self, project_id: str):
        self.created_projects.append(project_id)

    def cleanup_all(self):
        """Verwijder alle test data"""
        for project_id in self.created_projects:
            # DELETE /api/projects/{project_id}
            pass
        for session_id in self.created_sessions:
            # DELETE /api/sessions/{session_id}
            pass
```

**Checkpoint Zaterdag:** Mooie rapporten, individuele test runs, cleanup werkend

---

## Dag 4: Zondag 25 januari - Dry Runs & Dress Rehearsal

### Ochtend (09:00 - 12:00)

#### 4.1 Testrun #1 op Demo Machine
- [ ] Backend starten: `uvicorn app.main:app --reload`
- [ ] Alle tests draaien: `pytest backend/tests/e2e/ -v`
- [ ] Verify: alle tests PASS
- [ ] Cleanup uitvoeren
- [ ] Verify: geen test data meer in database

#### 4.2 Testrun #2 op Demo Machine
- [ ] Herhaal testrun
- [ ] Check voor flaky tests
- [ ] Timing noteren (voor demo planning)

### Middag (13:00 - 17:00)

#### 4.3 Testrun #3 op Demo Machine
- [ ] Finale testrun
- [ ] Screenshot alle resultaten
- [ ] Backup test rapporten

#### 4.4 Cleanup Verificatie
```sql
-- Verify geen test data in database
SELECT COUNT(*) FROM projects WHERE name LIKE 'TEST_%';
SELECT COUNT(*) FROM sessions WHERE project_id IN (SELECT id FROM projects WHERE name LIKE 'TEST_%');
-- Beide moeten 0 zijn
```

### Avond (19:00 - 21:00)

#### 4.5 Dress Rehearsal
- [ ] Volledige demo doorlopen alsof het maandag is
- [ ] Timing: max 30 minuten voor demo
- [ ] Backup plan als iets faalt
- [ ] Demo script voorbereiden

**Checkpoint Zondag:** 3x succesvol gedraaid, systeem schoon, klaar voor demo

---

## Demo Script: Maandag 26 januari 11:00

### Opening (2 min)
```
"Welkom bij de MarQed E2E Test Demo.
Vandaag toon ik hoe we Playwright gebruiken voor
geautomatiseerde end-to-end tests van ons platform."
```

### Demo Flow (25 min)

#### Part 1: Test Suite Overview (5 min)
- Toon test structuur in IDE
- Leg Page Object Model uit
- Toon conftest.py configuratie

#### Part 2: Individuele Test Run (10 min)
```bash
# Live demo: TC001 Project Intake
pytest backend/tests/e2e/tests/test_tc001_project_intake.py -v --headed --slowmo=300
```
- Browser opent zichtbaar
- Stappen worden uitgevoerd
- Assertions passeren
- Screenshot wordt genomen

#### Part 3: Full Suite Run (5 min)
```bash
# Alle tests parallel
pytest backend/tests/e2e/ -v -n auto
```
- Toon parallelle executie
- Toon HTML rapport

#### Part 4: Cleanup Demo (5 min)
```bash
# Toon dat systeem schoon is
python scripts/verify_cleanup.py
```
- Database query: 0 test records
- Filesystem: geen temp files

### Closing (3 min)
```
"Dit demonstreert hoe MarQed E2E tests:
1. Deterministic en herhaalbaar zijn
2. Individueel of samen kunnen draaien
3. Mooie rapporten genereren
4. Het systeem schoon achterlaten"
```

---

## Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Backend niet beschikbaar | HIGH | Lokaal testen, backup video |
| Flaky test tijdens demo | MEDIUM | 3x dry run, skip flaky tests |
| Browser crash | LOW | Fallback naar headless + screenshot |
| Database connectie faalt | MEDIUM | SQLite fallback voor demo |

---

## Backup Plan

**Als live demo faalt:**
1. Toon pre-recorded video van testrun
2. Toon HTML rapport van succesvolle run
3. Toon code en leg concepten uit

**Video backup locatie:** `docs/demo/e2e-demo-backup.mp4`

---

## Checklist per Dag

### Donderdag EOD
- [ ] Playwright geïnstalleerd en werkend
- [ ] Project structuur opgezet
- [ ] TC001 test werkend
- [ ] TC101 test werkend
- [ ] Dry run #1 door Claude: PASS

### Vrijdag EOD
- [ ] Alle 8 tests geconverteerd
- [ ] Elke test individueel uitvoerbaar
- [ ] Dry run #2 door Claude: PASS
- [ ] Geen flaky tests

### Zaterdag EOD
- [ ] HTML rapport configuratie klaar
- [ ] Demo scripts werkend
- [ ] Cleanup mechanisme getest
- [ ] Headed mode werkt met slowmo

### Zondag EOD
- [ ] Testrun #1 op demo machine: PASS
- [ ] Testrun #2 op demo machine: PASS
- [ ] Testrun #3 op demo machine: PASS
- [ ] Cleanup verificatie: 0 test data
- [ ] Dress rehearsal: PASS
- [ ] Backup video opgenomen

### Maandag 10:30
- [ ] Backend draait
- [ ] Browser getest
- [ ] Demo script bij de hand
- [ ] Backup plan klaar

---

## Technische Specificaties

### Test Conventies

```python
# Elke test heeft:
# 1. Duidelijke naam: test_tc001_project_intake_happy_path
# 2. Docstring met testcase ID
# 3. Cleanup in fixture
# 4. Screenshots op key moments

def test_tc001_project_intake_happy_path(page: Page, cleanup: TestDataCleaner):
    """
    TC001: Project Intake Flow

    Stappen:
    1. Open project intake pagina
    2. Vul project gegevens in
    3. Start intake
    4. Verify resultaat
    """
    # Test implementatie
    pass
```

### CLI Commands voor Demo

```bash
# Individuele test
pytest backend/tests/e2e/tests/test_tc001_project_intake.py -v --headed

# Specifieke test functie
pytest backend/tests/e2e/ -k "test_tc001" -v --headed

# Alle tests met rapport
pytest backend/tests/e2e/ -v --html=reports/demo-report.html

# Parallelle executie
pytest backend/tests/e2e/ -v -n 4

# Met slowmo voor demo
pytest backend/tests/e2e/tests/test_tc001_project_intake.py -v --headed --slowmo=500
```

### Cleanup Verificatie Script

```python
# scripts/verify_cleanup.py
import asyncio
from app.database import get_db

async def verify_no_test_data():
    async with get_db() as db:
        # Check projects
        result = await db.execute(
            "SELECT COUNT(*) FROM projects WHERE name LIKE 'TEST_%'"
        )
        project_count = result.scalar()

        # Check sessions
        result = await db.execute(
            "SELECT COUNT(*) FROM marqed_sessions WHERE id LIKE 'test-%'"
        )
        session_count = result.scalar()

        print(f"Test projects: {project_count}")
        print(f"Test sessions: {session_count}")

        if project_count == 0 and session_count == 0:
            print("✅ Systeem is schoon!")
            return True
        else:
            print("❌ Test data gevonden!")
            return False

if __name__ == "__main__":
    asyncio.run(verify_no_test_data())
```

---

## Success Criteria voor Demo

| Criterium | Requirement |
|-----------|-------------|
| Alle tests PASS | 8/8 tests groen |
| Individueel uitvoerbaar | `pytest -k "tc001"` werkt |
| Mooi rapport | HTML met screenshots |
| Live browser zichtbaar | `--headed` mode |
| Systeem schoon na tests | 0 test records |
| Demo binnen 30 min | Timing gerespecteerd |

---

*Document gegenereerd: 2026-01-22*
*Gebaseerd op: docs/E2E-TESTING-STRATEGY-ADVICE.md*
