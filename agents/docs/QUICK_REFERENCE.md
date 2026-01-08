# Quality Gates - Quick Reference Card

## 🚀 Essential Commands

### Quality Checks
```bash
# Basic check on staged files
npm run quality:check

# Detailed output with category scores
npm run quality:check:verbose

# Strict mode (requires 70% score)
npm run quality:check:strict

# Skip test checks (faster)
npm run quality:check:skip-tests
```

### Dashboard
```bash
# Generate dashboard data
npm run dashboard:generate

# Serve dashboard (http://localhost:8080)
npm run dashboard:serve

# Export as CSV
npm run dashboard:export:csv
```

### Git Operations
```bash
# Normal commit (hooks run automatically)
git commit -m "Your message"

# Emergency bypass (use sparingly!)
git commit --no-verify -m "Emergency fix"

# Disable hooks globally
export HUSKY=0
```

---

## 📊 Quality Categories (8)

| Category | Focus | Target |
|----------|-------|--------|
| **SIG-TOP-10** | Complexity, duplication, parameters | 90%+ |
| **SOLID** | Single Responsibility, OCP, LSP | 85%+ |
| **GRASP** | Information Expert, High Cohesion | 85%+ |
| **TDD** | Tests exist, written first | 80%+ |
| **Testing Patterns** | AAA, F.I.R.S.T, Test Pyramid | 80%+ |
| **Design Patterns** | Factory, Builder, Strategy | 85%+ |
| **Clean Code** | YAGNI, KISS, No magic numbers | 85%+ |
| **Law of Demeter** | Limited call chains | 90%+ |

---

## ⚠️ Severity Levels

| Level | Icon | Action | Examples |
|-------|------|--------|----------|
| **Critical** | 🚨 | Fix immediately | High complexity, No tests |
| **High** | ❌ | Fix before PR | SRP violation, Missing patterns |
| **Medium** | ⚠️ | Fix when possible | Magic numbers, AAA pattern |
| **Low** | ℹ️ | Nice to have | Call chains, Minor naming |

---

## 🔧 Common Fixes

### High Cyclomatic Complexity
```typescript
// ❌ Before: Complexity 12
if (x) { if (y) { if (z) { ... } } }

// ✅ After: Complexity 3
function main() { return check1() && check2() && check3(); }
```

### Missing Tests
```typescript
// Create tests/YourFile.test.ts
describe('YourClass', () => {
  it('should do something', () => {
    expect(result).toBe(expected);
  });
});
```

### Magic Numbers
```typescript
// ❌ Before
if (age > 18) { ... }

// ✅ After
const LEGAL_AGE = 18;
if (age > LEGAL_AGE) { ... }
```

### SRP Violation
```typescript
// ❌ Before: One class does everything
class User { validate() {} save() {} email() {} }

// ✅ After: Separate concerns
class UserValidator { validate() {} }
class UserRepository { save() {} }
class EmailService { send() {} }
```

---

## 📈 Dashboard Quick Guide

### Key Metrics
- **Overall Score**: Aim for 85%+
- **Critical Issues**: Keep at 0
- **Total Violations**: Trend downward
- **Files Checked**: Track coverage

### Charts
1. **Radar**: Category compliance (balanced = good)
2. **Doughnut**: Severity distribution (green = good)
3. **Line**: Quality trend (upward = good)
4. **Bar**: Check coverage (full = good)

### Actions
- 🔄 **Refresh**: Re-run checks
- 📊 **Export**: Download report
- ▶️ **Run**: Execute check

---

## 🆘 Troubleshooting

### Hook Not Running
```bash
# Check config
git config --get core.hooksPath
# Should be: .husky

# If not set:
git config core.hooksPath .husky
```

### Permission Denied
```bash
chmod +x .husky/pre-commit
chmod +x .husky/_/husky.sh
```

### ts-node Not Found
```bash
cd backend/agents
npm install
```

### Port 8080 In Use
```bash
# Find process
lsof -i :8080

# Kill it
kill -9 <PID>
```

---

## 📚 Documentation Locations

| Document | Purpose |
|----------|---------|
| `DEVELOPER_ONBOARDING.md` | "By design" quality approach |
| `QUALITY_GATE_USAGE_GUIDE.md` | Complete usage guide |
| `QUALITY_GATE_CONFIGURATION.md` | Config options |
| `TEAM_TRAINING_GUIDE.md` | Team training materials |
| `QUICK_REFERENCE.md` | This cheatsheet |

---

## 💡 Pro Tips

1. **Commit often** - Smaller commits = faster checks
2. **Fix as you go** - Don't accumulate violations
3. **Learn from findings** - Recommendations teach best practices
4. **Check dashboard daily** - Monitor trends
5. **Ask for help** - Use #quality-gates Slack

---

## 🎯 Success Formula

```
Quality Code = TDD + SOLID + Clean Code + Testing
```

**Remember:**
1. Write test first (RED)
2. Write minimal code (GREEN)
3. Refactor (REFACTOR)
4. Check quality gates
5. Commit
6. Repeat

---

## 📞 Quick Contacts

- **Slack**: #quality-gates
- **Office Hours**: Tuesdays 3-4 PM
- **Docs**: backend/agents/docs/
- **Dashboard**: http://localhost:8080

---

*Version 1.0 | Updated: 2025-11-15*
*Print this card and keep it handy! 📋*
