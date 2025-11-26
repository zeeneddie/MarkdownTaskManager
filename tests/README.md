# 🧪 E2E Tests - Multi-Stack AI Agent Platform

Geautomatiseerde End-to-End tests met Playwright voor het Multi-Stack AI Agent Platform project.

## 📋 Wat wordt getest?

### Test Suite: Drill-Down Navigation

**File:** `e2e/drill-down.spec.js`

**Coverage:**
- ✅ Epic → Feature drill-down met single click
- ✅ Feature → Story drill-down met single click
- ✅ Story → Task details (geen drill-down)
- ✅ "← Terug" navigatie door alle levels
- ✅ Direct Epic selectie vanuit elk level
- ✅ Double-click regression test (mag geen errors geven)
- ✅ UI teksten (geen "dubbelklik" meer)
- ✅ Rapid clicking graceful handling
- ✅ Mobile viewport support (tap events)

**Total Tests:** 10
**Browsers:** Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari

---

## 🚀 Quick Start

### 1. Installeer Dependencies

```bash
cd /home/eddie/Projects/MarkdownTaskManager/tests
npm install
```

### 2. Installeer Browsers

```bash
npm run install:browsers
```

Dit installeert Chromium, Firefox en WebKit (Safari).

### 3. Run Tests

**Alle tests (headless):**
```bash
npm test
```

**Alle tests (met browser venster):**
```bash
npm run test:headed
```

**Alleen drill-down tests:**
```bash
npm run test:drill-down
```

**Debug mode:**
```bash
npm run test:debug
```

**Interactive UI mode:**
```bash
npm run test:ui
```

---

## 📊 Test Results

### HTML Report

Na het runnen van tests, bekijk het HTML report:

```bash
npm run test:report
```

Dit opent een interactieve HTML report in je browser met:
- Test results per browser
- Screenshots van failures
- Video recordings van failures
- Traces voor debugging

### Screenshots

Screenshots worden opgeslagen in: `tests/screenshots/`

Gegenereerde screenshots:
- `drill-down-features.png` - Feature level view
- `drill-down-stories.png` - Story level view
- `task-details.png` - Task details view
- `back-navigation.png` - Back navigation result
- `mobile-drill-down.png` - Mobile viewport view

---

## 🎯 Test Scenarios

### Scenario 1: Basic Drill-Down

```javascript
test('should drill down from Epic to Features with single click')
```

**Stappen:**
1. Start op Epic level
2. Single click op Epic in sidebar
3. Single click op Feature card rechts
4. **Verwacht:** Sidebar toont nu Features, main panel toont Stories

### Scenario 2: Full Navigation Path

```javascript
test('should drill down from Feature to Stories with single click')
```

**Stappen:**
1. Epic → Feature (single click)
2. Feature → Story (single click)
3. **Verwacht:** Sidebar toont Stories, main panel toont Tasks

### Scenario 3: Back Navigation

```javascript
test('should navigate back correctly with Back button')
```

**Stappen:**
1. Navigeer naar Story level (3 levels deep)
2. Klik "← Terug" 3x
3. **Verwacht:** Terug bij Epics, Back knop verdwijnt

### Scenario 4: Regression Test

```javascript
test('should not have double-click handlers (regression test)')
```

**Test:** Double-click mag geen errors geven
**Verwacht:** Geen JavaScript errors, navigatie werkt

---

## 🔧 Configuration

### Playwright Config

**File:** `playwright.config.js`

**Belangrijke settings:**
```javascript
{
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  retries: 2, // Op CI
  webServer: {
    command: 'cd ../backend && uvicorn ...',
    url: 'http://localhost:8000/api/health',
    reuseExistingServer: true
  }
}
```

### Browsers

Tests draaien op:
- ✅ Chromium (Desktop Chrome/Edge)
- ✅ Firefox
- ✅ WebKit (Desktop Safari)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)

---

## 📝 Test Structure

```
tests/
├── package.json              # Dependencies & scripts
├── playwright.config.js      # Playwright configuration
├── README.md                 # This file
├── e2e/
│   └── drill-down.spec.js   # Drill-down navigation tests
├── screenshots/              # Test screenshots
│   ├── drill-down-features.png
│   ├── drill-down-stories.png
│   ├── task-details.png
│   ├── back-navigation.png
│   └── mobile-drill-down.png
└── test-results/             # Generated test results
    ├── html/                 # HTML report
    ├── results.json          # JSON results
    └── videos/               # Failure videos
```

---

## 🐛 Troubleshooting

### Backend niet gestart

**Symptom:** Tests falen met "net::ERR_CONNECTION_REFUSED"

**Fix:**
```bash
# Start backend manually
cd /home/eddie/Projects/MarkdownTaskManager/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Of: De `webServer` config in `playwright.config.js` zorgt automatisch voor backend start.

### PostgreSQL niet gestart

**Symptom:** Backend start maar API geeft database errors

**Fix:**
```bash
pg_isready
sudo systemctl start postgresql
```

### Browsers niet geïnstalleerd

**Symptom:** "Executable doesn't exist at ..."

**Fix:**
```bash
npm run install:browsers
```

### Tests timeout

**Symptom:** "Test timeout of 30000ms exceeded"

**Fix:**
Verhoog timeout in test:
```javascript
test('my test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ...
});
```

---

## 📈 CI/CD Integration

### GitHub Actions

**Example workflow:**

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup PostgreSQL
        run: |
          sudo systemctl start postgresql
          sudo -u postgres psql -c "CREATE DATABASE project_manager;"

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Backend Dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Test Dependencies
        run: |
          cd tests
          npm install
          npx playwright install --with-deps

      - name: Run E2E Tests
        run: |
          cd tests
          npm test

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/test-results/html/
```

---

## 🔄 Continuous Testing

### Watch Mode (Development)

Voor development, run tests in watch mode:

```bash
npm test -- --watch
```

Dit herstart tests automatisch bij code changes.

### Specific Browser

Run alleen op Chrome:
```bash
npm test -- --project=chromium
```

Run alleen op Mobile:
```bash
npm test -- --project="Mobile Chrome"
```

---

## 📚 Playwright Resources

**Documentation:**
- Official Docs: https://playwright.dev/
- Best Practices: https://playwright.dev/docs/best-practices
- Selectors: https://playwright.dev/docs/selectors

**Useful Commands:**
```bash
# Generate tests interactively
npx playwright codegen http://localhost:8000/

# Show trace viewer
npx playwright show-trace trace.zip

# Update snapshots
npm test -- --update-snapshots
```

---

## ✅ Success Criteria

De tests slagen als:
- ✅ Alle 10 tests zijn groen
- ✅ 0 JavaScript errors in console
- ✅ Screenshots tonen correcte UI state
- ✅ Tests werken op alle 5 browsers
- ✅ Mobile tests werken met tap events
- ✅ Execution time <2 minuten

---

## 🎯 Next Steps

**Fase 5 (Week 19):** Test Automation Expansion
- Unit tests voor backend (pytest)
- Integration tests voor API
- More E2E scenarios (Sprint Planning, etc.)
- Visual regression tests
- Performance tests

**See:** `fasenplan.md` → Fase 5: Quality & Testing

---

## 📞 Support

**Issues?**
- Check troubleshooting section above
- Open browser console during tests (headed mode)
- Use debug mode: `npm run test:debug`
- Check Playwright traces in HTML report

---

**Last Updated:** 2025-11-12
**Author:** Eddie
**Version:** 1.0.0
