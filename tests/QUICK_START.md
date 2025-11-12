# 🚀 Quick Start - E2E Tests

5-minuten setup voor automated testing!

---

## ⚡ Super Quick Start

```bash
# 1. Install dependencies (first time only)
./run-tests.sh install

# 2. Run tests
./run-tests.sh test

# 3. View results
./run-tests.sh report
```

**Done!** ✅

---

## 📋 One-Liner Install

```bash
cd /home/eddie/Projects/MarkdownTaskManager && ./run-tests.sh install
```

---

## 🎯 Common Commands

### Run Tests

```bash
# Headless (fastest, no browser window)
./run-tests.sh test

# Headed (see what's happening)
./run-tests.sh headed

# Only drill-down tests
./run-tests.sh drill-down
```

### View Results

```bash
# Open HTML report
./run-tests.sh report
```

### Debug

```bash
# Step-by-step debugging
./run-tests.sh debug

# Interactive UI
./run-tests.sh ui
```

### Clean Up

```bash
# Remove test results
./run-tests.sh clean
```

---

## 🔍 What Gets Tested?

✅ **10 Tests** covering:
- Epic → Feature drill-down
- Feature → Story drill-down
- Story → Task details
- Back navigation
- Direct Epic selection
- Double-click regression
- UI text validation
- Rapid clicking
- Mobile support

✅ **5 Browsers**:
- Chrome (Desktop)
- Firefox (Desktop)
- Safari (Desktop)
- Chrome (Mobile)
- Safari (Mobile)

---

## 📊 Test Output

### Console Output
```
Running 10 tests using 1 worker

  ✓  [chromium] › drill-down.spec.js:18 should display initial epic list
  ✓  [chromium] › drill-down.spec.js:35 should drill down from Epic to Features
  ✓  [chromium] › drill-down.spec.js:68 should drill down from Feature to Stories
  ...

  10 passed (45s)
```

### HTML Report
- Interactive results browser
- Screenshots on failure
- Video recordings
- Execution traces

---

## 🐛 Troubleshooting

### "PostgreSQL not running"
```bash
sudo systemctl start postgresql
```

### "Dependencies not installed"
```bash
./run-tests.sh install
```

### "Tests failing"
```bash
# Debug mode
./run-tests.sh debug

# Check browser console
./run-tests.sh headed
```

---

## 📁 File Structure

```
tests/
├── run-tests.sh              ← Main test runner
├── package.json              ← Dependencies
├── playwright.config.js      ← Config
├── README.md                 ← Full docs
├── QUICK_START.md            ← This file
└── e2e/
    └── drill-down.spec.js    ← Test suite
```

---

## ✅ Success Checklist

First time setup:
- [ ] Run `./run-tests.sh install`
- [ ] PostgreSQL is running
- [ ] Backend can start
- [ ] Run `./run-tests.sh test`
- [ ] All tests pass ✅
- [ ] View report works

---

## 🎓 Learn More

**Full Documentation:** `tests/README.md`
**Playwright Docs:** https://playwright.dev/

---

**Need help?** Check the full README.md or troubleshooting section!
