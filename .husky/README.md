# Husky Git Hooks

This directory contains Git hooks managed by [Husky](https://typicode.github.io/husky/).

## What Are Git Hooks?

Git hooks are scripts that run automatically at certain points in the Git workflow (e.g., before commits, before pushes). They help maintain code quality and consistency.

## Current Hooks

### pre-commit

**Purpose**: Runs quality checks on staged files before allowing commits.

**What it does**:
1. Gets list of staged TypeScript/JavaScript files
2. Runs QualityGateService quality checks on those files
3. Blocks commit if critical violations are found
4. Displays detailed feedback with recommendations

**Location**: `.husky/pre-commit`

## How to Use

### Normal Workflow (Hooks Run Automatically)

```bash
# Stage your changes
git add src/UserService.ts

# Commit (hook runs automatically)
git commit -m "Add user service"

# If quality checks pass:
# ✅ Commit proceeds

# If quality checks fail:
# ❌ Commit is blocked
# Fix the issues and try again
```

### Bypass Hooks (Use Sparingly!)

```bash
# Emergency commits only - bypasses all quality checks
git commit --no-verify -m "Emergency hotfix"

# Or use environment variable
HUSKY=0 git commit -m "Skip hooks"
```

### Run Checks Manually

```bash
# From backend/agents directory:
npm run quality:check              # Basic check
npm run quality:check:verbose      # Detailed output
npm run quality:check:strict       # Require 70% quality score
npm run quality:check:skip-tests   # Skip TDD checks (faster)
```

## Setup for New Developers

### Automatic (Recommended)

```bash
# Install dependencies (runs husky install automatically)
cd backend/agents
npm install

# Hooks are now active!
```

### Manual (If Needed)

```bash
# Configure git to use .husky directory
git config core.hooksPath .husky

# Verify
git config --get core.hooksPath
# Should output: .husky
```

## Troubleshooting

### Hook Not Running

```bash
# Check git config
git config --get core.hooksPath
# Should be: .husky

# If not set:
git config core.hooksPath .husky
```

### Hook Permission Denied

```bash
# Make hooks executable
chmod +x .husky/pre-commit
chmod +x .husky/_/husky.sh
```

### ts-node Command Not Found

```bash
# Install dependencies
cd backend/agents
npm install
```

## Files in This Directory

```
.husky/
├── README.md          # This file
├── _/
│   └── husky.sh      # Husky helper script (don't modify)
└── pre-commit        # Pre-commit hook (runs quality checks)
```

## Configuration

To modify pre-commit behavior, edit:
- **Hook script**: `.husky/pre-commit`
- **Quality check logic**: `backend/agents/scripts/pre-commit-quality-check.ts`

## Documentation

For detailed documentation on the quality checks, see:
- `backend/agents/docs/WEEK_12_DAY_1_2_SUMMARY.md` - Pre-commit hooks guide
- `backend/agents/docs/QUALITY_GATE_USAGE_GUIDE.md` - Quality gate usage
- `backend/agents/docs/QUALITY_GATE_CONFIGURATION.md` - Configuration options

## Why Husky?

Husky makes it easy to:
- ✅ Share Git hooks with the team
- ✅ Ensure consistent quality across all commits
- ✅ Catch issues before code review
- ✅ Enforce team standards automatically

---

**Week 12 Day 1-2**: Pre-commit Hooks Implementation
**Status**: ✅ COMPLETE
**Date**: 2025-11-15
