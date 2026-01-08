# Quality Assessment CI/CD Integration

**Datum:** 2025-12-31
**Week:** 129
**Doel:** Vergelijkbare kwaliteitsmetrieken voor dual-stack migratie (.NET 8/Blazor vs Django/React)

---

## 1. Quality Assessment Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  DUAL-STACK QUALITY ASSESSMENT PIPELINE                                                  │
│                                                                                          │
│  ┌─────────────────────────────────┐      ┌─────────────────────────────────┐           │
│  │  STACK A: .NET 8/Blazor         │      │  STACK B: Django/React          │           │
│  │  Pipeline: stack-a.yml          │      │  Pipeline: stack-b.yml          │           │
│  └──────────────┬──────────────────┘      └──────────────┬──────────────────┘           │
│                 │                                         │                              │
│                 ▼                                         ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                         QUALITY ASSESSMENT STAGES                                    ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ││
│  │  │  LOC    │ │ Balance │ │Complexity│ │ Tests  │ │Security │ │  Deps   │ │ Docs   │ ││
│  │  │ Metrics │ │ Analysis│ │ Profile │ │Coverage│ │  Scan   │ │ Health  │ │ Score  │ ││
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └───┬────┘ └────┬────┘ └────┬────┘ └───┬────┘ ││
│  │       │           │           │          │           │           │          │       ││
│  │       └───────────┴───────────┴──────────┴───────────┴───────────┴──────────┘       ││
│  │                                          │                                           ││
│  │                                          ▼                                           ││
│  │                          ┌───────────────────────────────┐                           ││
│  │                          │  UNIFIED QUALITY REPORT       │                           ││
│  │                          │  quality-report.json          │                           ││
│  │                          │  quality-comparison.md        │                           ││
│  │                          └───────────────────────────────┘                           ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                          │                                               │
│                                          ▼                                               │
│                          ┌───────────────────────────────┐                              │
│                          │  COMPARISON DASHBOARD         │                              │
│                          │  Stack A vs Stack B           │                              │
│                          │  Winner per Category          │                              │
│                          └───────────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Quality Metrics Categories

### 2.1 Complete Metrics Matrix

| Category | Metric | Stack A Tool | Stack B Tool | Weight | Threshold |
|----------|--------|--------------|--------------|--------|-----------|
| **LOC Metrics** | Total Lines of Code | cloc | cloc | - | Informational |
| | Code Lines (excl. comments) | cloc | cloc | - | Informational |
| | Comment Ratio | cloc | cloc | 5% | >= 10% |
| | Blank Line Ratio | cloc | cloc | - | Informational |
| **Code Balance** | Files per Module | dotnet sln | Django apps | 5% | Even distribution |
| | LOC per File (avg) | cloc + calc | cloc + calc | 5% | <= 300 |
| | LOC per File (max) | cloc + calc | cloc + calc | - | <= 500 |
| | Function Length (avg) | Roslyn | ast | 5% | <= 30 lines |
| **Complexity** | Cyclomatic Complexity (avg) | dotnet-metrics | radon | 10% | <= 10 |
| | Cyclomatic Complexity (max) | dotnet-metrics | radon | 5% | <= 25 |
| | High Complexity Count (>15) | dotnet-metrics | radon | 5% | 0 |
| | Nesting Depth (max) | Roslyn | ast | 5% | <= 4 |
| **Test Coverage** | Line Coverage | dotnet test + coverlet | pytest-cov | 15% | >= 80% |
| | Branch Coverage | coverlet | pytest-cov | 10% | >= 70% |
| | Test Count | dotnet test | pytest | - | Informational |
| | Test/Code Ratio | calculated | calculated | 5% | >= 0.5 |
| **Security** | Critical Issues | Snyk/Semgrep | Bandit/Snyk | 10% | 0 |
| | High Issues | Snyk/Semgrep | Bandit/Snyk | 5% | 0 |
| | Medium Issues | Snyk/Semgrep | Bandit/Snyk | 2.5% | <= 5 |
| | Dependency Vulnerabilities | dotnet audit | pip-audit | 5% | 0 critical |
| **Dependencies** | Direct Dependencies | nuget | pip | - | Informational |
| | Outdated Dependencies | dotnet outdated | pip-outdated | 2.5% | <= 10% |
| | Circular Dependencies | dotnet-depends | pydeps | 5% | 0 |
| | Unused Dependencies | depcheck | pip-autoremove | 2.5% | 0 |
| **Documentation** | README Score | custom | custom | 2.5% | >= 80% |
| | API Doc Coverage | docfx | sphinx | 5% | >= 70% |
| | Inline Comment Ratio | cloc | cloc | 2.5% | >= 10% |
| **Maintainability** | Tech Debt (days) | SonarQube | SonarQube | 5% | <= 5 days |
| | Code Duplication | jscpd | jscpd | 5% | <= 3% |
| | Maintainability Index | Roslyn | radon | 5% | >= 65 |

**Total Weight:** 100%

---

## 3. Stack-Specific Tool Configuration

### 3.1 Stack A: .NET 8/Blazor Tools

```yaml
# .github/workflows/stack-a-quality.yml
quality_tools:
  loc:
    tool: cloc
    command: "cloc src/ --json --out=metrics/loc.json"

  complexity:
    tool: dotnet-metrics
    command: "dotnet tool run dotnet-metrics src/ -o metrics/complexity.json"

  coverage:
    tool: coverlet
    command: "dotnet test --collect:'XPlat Code Coverage' --results-directory ./coverage"
    report: "reportgenerator -reports:coverage/**/coverage.cobertura.xml -targetdir:coverage/report"

  security:
    - tool: snyk
      command: "snyk test --json > metrics/snyk.json"
    - tool: semgrep
      command: "semgrep --config auto src/ --json -o metrics/semgrep.json"

  dependencies:
    tool: dotnet-outdated
    command: "dotnet outdated -o metrics/deps.json"

  duplication:
    tool: jscpd
    command: "jscpd src/ --reporters json --output metrics/duplication"

  maintainability:
    tool: sonarqube
    command: "dotnet sonarscanner begin && dotnet build && dotnet sonarscanner end"
```

### 3.2 Stack B: Django/React Tools

```yaml
# .github/workflows/stack-b-quality.yml
quality_tools:
  loc:
    tool: cloc
    command: "cloc backend/ frontend/ --json --out=metrics/loc.json"

  complexity:
    tool: radon
    command: "radon cc backend/ -j > metrics/complexity.json && radon mi backend/ -j > metrics/maintainability.json"

  coverage:
    tool: pytest-cov
    command: "pytest --cov=backend --cov-report=json:metrics/coverage.json --cov-report=html:coverage/"
    frontend: "npm run test:coverage -- --coverageReporters=json --coverageDirectory=coverage"

  security:
    - tool: bandit
      command: "bandit -r backend/ -f json -o metrics/bandit.json"
    - tool: snyk
      command: "snyk test --json > metrics/snyk.json"
    - tool: npm-audit
      command: "cd frontend && npm audit --json > ../metrics/npm-audit.json"

  dependencies:
    - tool: pip-outdated
      command: "pip list --outdated --format=json > metrics/pip-outdated.json"
    - tool: npm-outdated
      command: "cd frontend && npm outdated --json > ../metrics/npm-outdated.json"

  duplication:
    tool: jscpd
    command: "jscpd backend/ frontend/src/ --reporters json --output metrics/duplication"

  maintainability:
    tool: sonarqube
    command: "sonar-scanner"
```

---

## 4. Unified Quality Report Format

### 4.1 JSON Schema

```json
{
  "$schema": "quality-report-schema.json",
  "stack": "stack-a | stack-b",
  "version": "1.0.0",
  "timestamp": "2025-12-31T12:00:00Z",
  "commit_sha": "abc123",
  "branch": "main",

  "summary": {
    "overall_score": 85.5,
    "grade": "B+",
    "pass": true,
    "categories_passed": 6,
    "categories_failed": 1
  },

  "categories": {
    "loc_metrics": {
      "score": 100,
      "weight": 0.05,
      "weighted_score": 5.0,
      "metrics": {
        "total_lines": 12605,
        "code_lines": 9840,
        "comment_lines": 1265,
        "blank_lines": 1500,
        "comment_ratio": 0.128,
        "files_count": 87
      }
    },

    "code_balance": {
      "score": 78,
      "weight": 0.15,
      "weighted_score": 11.7,
      "metrics": {
        "avg_loc_per_file": 113,
        "max_loc_per_file": 456,
        "avg_function_length": 22,
        "max_function_length": 89,
        "modules_count": 12,
        "files_per_module_stddev": 2.3
      }
    },

    "complexity": {
      "score": 72,
      "weight": 0.25,
      "weighted_score": 18.0,
      "metrics": {
        "avg_cyclomatic": 8.5,
        "max_cyclomatic": 28,
        "high_complexity_count": 3,
        "max_nesting_depth": 5,
        "cognitive_complexity_avg": 12.3
      }
    },

    "test_coverage": {
      "score": 85,
      "weight": 0.25,
      "weighted_score": 21.25,
      "metrics": {
        "line_coverage": 82.5,
        "branch_coverage": 71.2,
        "test_count": 156,
        "test_code_ratio": 0.65,
        "mutation_score": null
      }
    },

    "security": {
      "score": 95,
      "weight": 0.175,
      "weighted_score": 16.625,
      "metrics": {
        "critical_issues": 0,
        "high_issues": 0,
        "medium_issues": 2,
        "low_issues": 8,
        "info_issues": 12,
        "dependency_vulnerabilities": {
          "critical": 0,
          "high": 1,
          "medium": 3
        }
      }
    },

    "dependencies": {
      "score": 88,
      "weight": 0.10,
      "weighted_score": 8.8,
      "metrics": {
        "direct_dependencies": 24,
        "transitive_dependencies": 156,
        "outdated_count": 3,
        "outdated_ratio": 0.125,
        "circular_dependencies": 0,
        "unused_dependencies": 1
      }
    },

    "documentation": {
      "score": 65,
      "weight": 0.10,
      "weighted_score": 6.5,
      "metrics": {
        "readme_score": 75,
        "api_doc_coverage": 58,
        "inline_comment_ratio": 0.128,
        "changelog_exists": true,
        "contributing_exists": false
      }
    },

    "maintainability": {
      "score": 78,
      "weight": 0.15,
      "weighted_score": 11.7,
      "metrics": {
        "tech_debt_days": 3.2,
        "code_duplication_ratio": 0.024,
        "maintainability_index": 68.5,
        "code_smells": 12
      }
    }
  },

  "issues": [
    {
      "category": "complexity",
      "severity": "warning",
      "metric": "max_cyclomatic",
      "value": 28,
      "threshold": 25,
      "file": "src/Services/AfspraakBLL.cs",
      "line": 145,
      "message": "Function ProcessAppointment has cyclomatic complexity 28 (threshold: 25)"
    }
  ],

  "trends": {
    "compared_to_previous": {
      "overall_score_delta": +2.3,
      "coverage_delta": +1.5,
      "tech_debt_delta": -0.5
    }
  }
}
```

### 4.2 Comparison Report Format

```markdown
# Quality Comparison Report: Stack A vs Stack B

**Date:** 2025-12-31
**Commit:** Stack A: abc123, Stack B: def456

## Overall Scores

| Stack | Score | Grade | Status |
|-------|-------|-------|--------|
| **Stack A** (.NET 8/Blazor) | 85.5 | B+ | ✅ PASS |
| **Stack B** (Django/React) | 82.3 | B | ✅ PASS |
| **Winner** | Stack A | +3.2 | |

## Category Breakdown

| Category | Weight | Stack A | Stack B | Winner | Delta |
|----------|--------|---------|---------|--------|-------|
| LOC Metrics | 5% | 100 | 100 | TIE | 0 |
| Code Balance | 15% | 78 | 82 | Stack B | +4 |
| Complexity | 25% | 72 | 75 | Stack B | +3 |
| Test Coverage | 25% | 85 | 80 | Stack A | +5 |
| Security | 17.5% | 95 | 92 | Stack A | +3 |
| Dependencies | 10% | 88 | 85 | Stack A | +3 |
| Documentation | 10% | 65 | 70 | Stack B | +5 |
| Maintainability | 15% | 78 | 76 | Stack A | +2 |

## Key Findings

### Stack A Strengths
- Higher test coverage (85% vs 80%)
- Better security posture (no high issues)
- Fewer outdated dependencies

### Stack B Strengths
- Lower complexity scores
- Better code balance
- Higher documentation coverage

## Recommendations

1. **Stack A:** Reduce complexity in AfspraakBLL.cs
2. **Stack B:** Increase test coverage to 85%
3. **Both:** Add CONTRIBUTING.md
```

---

## 5. CI/CD Pipeline Integration

### 5.1 Stack A Pipeline (.NET 8/Blazor)

```yaml
# .github/workflows/stack-a.yml
name: Stack A Quality Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'stack-a/**'
  pull_request:
    branches: [main]
    paths:
      - 'stack-a/**'

env:
  DOTNET_VERSION: '8.0.x'

jobs:
  # Stage 1: Build
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}
      - run: dotnet restore
      - run: dotnet build --no-restore

  # Stage 2: LOC Metrics
  loc-metrics:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Install cloc
        run: sudo apt-get install -y cloc
      - name: Run cloc
        run: |
          mkdir -p metrics
          cloc stack-a/src --json --out=metrics/loc.json
      - uses: actions/upload-artifact@v4
        with:
          name: loc-metrics
          path: metrics/loc.json

  # Stage 3: Complexity Analysis
  complexity:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}
      - name: Install dotnet-metrics
        run: dotnet tool install -g dotnet-metrics
      - name: Run complexity analysis
        run: |
          mkdir -p metrics
          dotnet-metrics stack-a/src -o metrics/complexity.json
      - uses: actions/upload-artifact@v4
        with:
          name: complexity-metrics
          path: metrics/complexity.json

  # Stage 4: Test Coverage
  test-coverage:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}
      - name: Run tests with coverage
        run: |
          dotnet test stack-a/tests \
            --collect:"XPlat Code Coverage" \
            --results-directory ./coverage \
            --logger "trx;LogFileName=test-results.trx"
      - name: Generate coverage report
        run: |
          dotnet tool install -g dotnet-reportgenerator-globaltool
          reportgenerator \
            -reports:coverage/**/coverage.cobertura.xml \
            -targetdir:coverage/report \
            -reporttypes:JsonSummary
          mkdir -p metrics
          cp coverage/report/Summary.json metrics/coverage.json
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-metrics
          path: |
            metrics/coverage.json
            coverage/report/

  # Stage 5: Security Scan
  security:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/dotnet@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --json-file-output=metrics/snyk.json
        continue-on-error: true
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: auto
          output: metrics/semgrep.json
      - uses: actions/upload-artifact@v4
        with:
          name: security-metrics
          path: metrics/

  # Stage 6: Dependency Analysis
  dependencies:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}
      - name: Check outdated packages
        run: |
          dotnet tool install -g dotnet-outdated-tool
          mkdir -p metrics
          dotnet outdated stack-a -o metrics/deps.json --output-format json
      - uses: actions/upload-artifact@v4
        with:
          name: dependency-metrics
          path: metrics/deps.json

  # Stage 7: Code Duplication
  duplication:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Run jscpd
        run: |
          npm install -g jscpd
          mkdir -p metrics
          jscpd stack-a/src --reporters json --output metrics/duplication
      - uses: actions/upload-artifact@v4
        with:
          name: duplication-metrics
          path: metrics/duplication/

  # Stage 8: Generate Quality Report
  quality-report:
    runs-on: ubuntu-latest
    needs: [loc-metrics, complexity, test-coverage, security, dependencies, duplication]
    steps:
      - uses: actions/checkout@v4
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: metrics/
      - name: Generate unified report
        run: |
          python scripts/generate-quality-report.py \
            --stack stack-a \
            --input-dir metrics/ \
            --output metrics/quality-report.json
      - name: Upload quality report
        uses: actions/upload-artifact@v4
        with:
          name: stack-a-quality-report
          path: metrics/quality-report.json
      - name: Post to MarQed API
        run: |
          curl -X POST ${{ secrets.MARQED_API_URL }}/api/quality/report \
            -H "Authorization: Bearer ${{ secrets.MARQED_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d @metrics/quality-report.json

  # Stage 9: Quality Gate Check
  quality-gate:
    runs-on: ubuntu-latest
    needs: quality-report
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: stack-a-quality-report
          path: metrics/
      - name: Check quality gate
        run: |
          python scripts/check-quality-gate.py \
            --report metrics/quality-report.json \
            --min-score 70 \
            --fail-on critical,high
```

### 5.2 Stack B Pipeline (Django/React)

```yaml
# .github/workflows/stack-b.yml
name: Stack B Quality Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'stack-b/**'
  pull_request:
    branches: [main]
    paths:
      - 'stack-b/**'

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'

jobs:
  # Stage 1: Build
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - name: Install backend dependencies
        run: |
          cd stack-b/backend
          pip install -r requirements.txt
      - name: Install frontend dependencies
        run: |
          cd stack-b/frontend
          npm ci

  # Stage 2: LOC Metrics
  loc-metrics:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Install cloc
        run: sudo apt-get install -y cloc
      - name: Run cloc
        run: |
          mkdir -p metrics
          cloc stack-b/backend stack-b/frontend/src --json --out=metrics/loc.json
      - uses: actions/upload-artifact@v4
        with:
          name: loc-metrics
          path: metrics/loc.json

  # Stage 3: Complexity Analysis
  complexity:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install radon
        run: pip install radon
      - name: Run complexity analysis
        run: |
          mkdir -p metrics
          radon cc stack-b/backend -j > metrics/complexity-cc.json
          radon mi stack-b/backend -j > metrics/complexity-mi.json
          # Combine reports
          python -c "
          import json
          cc = json.load(open('metrics/complexity-cc.json'))
          mi = json.load(open('metrics/complexity-mi.json'))
          combined = {'cyclomatic': cc, 'maintainability': mi}
          json.dump(combined, open('metrics/complexity.json', 'w'))
          "
      - uses: actions/upload-artifact@v4
        with:
          name: complexity-metrics
          path: metrics/complexity.json

  # Stage 4: Test Coverage
  test-coverage:
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - name: Backend tests with coverage
        run: |
          cd stack-b/backend
          pip install -r requirements.txt
          pytest --cov=. --cov-report=json:../../metrics/backend-coverage.json
      - name: Frontend tests with coverage
        run: |
          cd stack-b/frontend
          npm ci
          npm run test:coverage -- --coverageReporters=json
          cp coverage/coverage-final.json ../../metrics/frontend-coverage.json
      - name: Combine coverage reports
        run: |
          python scripts/combine-coverage.py \
            --backend metrics/backend-coverage.json \
            --frontend metrics/frontend-coverage.json \
            --output metrics/coverage.json
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-metrics
          path: metrics/coverage.json

  # Stage 5: Security Scan
  security:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Run Bandit
        run: |
          pip install bandit
          mkdir -p metrics
          bandit -r stack-b/backend -f json -o metrics/bandit.json || true
      - name: Run pip-audit
        run: |
          pip install pip-audit
          cd stack-b/backend
          pip-audit --format=json > ../metrics/pip-audit.json || true
      - name: Run npm audit
        run: |
          cd stack-b/frontend
          npm audit --json > ../metrics/npm-audit.json || true
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --json-file-output=metrics/snyk.json
        continue-on-error: true
      - uses: actions/upload-artifact@v4
        with:
          name: security-metrics
          path: metrics/

  # Stage 6: Dependency Analysis
  dependencies:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - name: Check outdated packages
        run: |
          mkdir -p metrics
          cd stack-b/backend
          pip install pip-tools
          pip list --outdated --format=json > ../../metrics/pip-outdated.json
          cd ../frontend
          npm outdated --json > ../../metrics/npm-outdated.json || true
      - uses: actions/upload-artifact@v4
        with:
          name: dependency-metrics
          path: metrics/

  # Stage 7: Code Duplication
  duplication:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - name: Run jscpd
        run: |
          npm install -g jscpd
          mkdir -p metrics
          jscpd stack-b/backend stack-b/frontend/src --reporters json --output metrics/duplication
      - uses: actions/upload-artifact@v4
        with:
          name: duplication-metrics
          path: metrics/duplication/

  # Stage 8: Generate Quality Report
  quality-report:
    runs-on: ubuntu-latest
    needs: [loc-metrics, complexity, test-coverage, security, dependencies, duplication]
    steps:
      - uses: actions/checkout@v4
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: metrics/
      - name: Generate unified report
        run: |
          python scripts/generate-quality-report.py \
            --stack stack-b \
            --input-dir metrics/ \
            --output metrics/quality-report.json
      - name: Upload quality report
        uses: actions/upload-artifact@v4
        with:
          name: stack-b-quality-report
          path: metrics/quality-report.json
      - name: Post to MarQed API
        run: |
          curl -X POST ${{ secrets.MARQED_API_URL }}/api/quality/report \
            -H "Authorization: Bearer ${{ secrets.MARQED_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d @metrics/quality-report.json

  # Stage 9: Quality Gate Check
  quality-gate:
    runs-on: ubuntu-latest
    needs: quality-report
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: stack-b-quality-report
          path: metrics/
      - name: Check quality gate
        run: |
          python scripts/check-quality-gate.py \
            --report metrics/quality-report.json \
            --min-score 70 \
            --fail-on critical,high
```

### 5.3 Comparison Pipeline

```yaml
# .github/workflows/quality-comparison.yml
name: Quality Comparison

on:
  workflow_run:
    workflows: ["Stack A Quality Pipeline", "Stack B Quality Pipeline"]
    types:
      - completed

jobs:
  compare:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4

      - name: Download Stack A report
        uses: dawidd6/action-download-artifact@v3
        with:
          workflow: stack-a.yml
          name: stack-a-quality-report
          path: metrics/stack-a/

      - name: Download Stack B report
        uses: dawidd6/action-download-artifact@v3
        with:
          workflow: stack-b.yml
          name: stack-b-quality-report
          path: metrics/stack-b/

      - name: Generate comparison report
        run: |
          python scripts/generate-comparison.py \
            --stack-a metrics/stack-a/quality-report.json \
            --stack-b metrics/stack-b/quality-report.json \
            --output metrics/comparison.md \
            --json-output metrics/comparison.json

      - name: Post comparison to MarQed
        run: |
          curl -X POST ${{ secrets.MARQED_API_URL }}/api/quality/comparison \
            -H "Authorization: Bearer ${{ secrets.MARQED_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d @metrics/comparison.json

      - name: Comment on PR (if applicable)
        if: github.event.workflow_run.event == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const comparison = fs.readFileSync('metrics/comparison.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comparison
            })
```

---

## 6. MarQed API Integration

### 6.1 New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quality/report` | POST | Submit quality report for a stack |
| `/api/quality/report/{stack}` | GET | Get latest report for a stack |
| `/api/quality/comparison` | POST | Submit comparison report |
| `/api/quality/comparison/latest` | GET | Get latest comparison |
| `/api/quality/trends/{stack}` | GET | Get quality trends over time |
| `/api/quality/dashboard` | GET | Get dashboard data for both stacks |

### 6.2 Dashboard Integration

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  QUALITY COMPARISON DASHBOARD                                                            │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │  OVERALL SCORES                                                                   │   │
│  │  ┌─────────────────────┐         ┌─────────────────────┐                         │   │
│  │  │  STACK A: 85.5     │         │  STACK B: 82.3      │                         │   │
│  │  │  .NET 8/Blazor     │         │  Django/React       │                         │   │
│  │  │  Grade: B+         │         │  Grade: B           │                         │   │
│  │  │  ████████████░░░░  │         │  ████████████░░░░░  │                         │   │
│  │  └─────────────────────┘         └─────────────────────┘                         │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │  CATEGORY COMPARISON (Radar Chart)                                                │   │
│  │                      Complexity                                                   │   │
│  │                         ▲                                                         │   │
│  │                        ╱ ╲                                                        │   │
│  │           Tests ──────●───●────── Security                                        │   │
│  │                      ╱     ╲                                                      │   │
│  │                     ╱       ╲                                                     │   │
│  │           Balance ●─────────● Dependencies                                        │   │
│  │                     ╲       ╱                                                     │   │
│  │                      ╲     ╱                                                      │   │
│  │           Docs ───────●───●────── Maintain                                        │   │
│  │                        ╲ ╱                                                        │   │
│  │                         ▼                                                         │   │
│  │                        LOC                                                        │   │
│  │                                                                                   │   │
│  │  ── Stack A (Blue)  ── Stack B (Green)                                           │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │  TRENDS OVER TIME                                                                 │   │
│  │  90 ┤                                   ●                                         │   │
│  │     │                           ●───────                                          │   │
│  │  85 ┤              ●────────────                                                  │   │
│  │     │      ●───────                                                               │   │
│  │  80 ┤──────                                                                       │   │
│  │     │                                                                             │   │
│  │  75 ┤                                                                             │   │
│  │     └────┬────┬────┬────┬────┬────┬────┬────                                     │   │
│  │         W1   W2   W3   W4   W5   W6   W7   W8                                    │   │
│  │                                                                                   │   │
│  │  ── Stack A (Blue)  ── Stack B (Green)                                           │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Quality Gate Thresholds

### 7.1 Blocking Thresholds (Build Fails)

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Critical Security Issues | 0 | Zero tolerance for critical vulns |
| High Security Issues | 0 | No high severity in production |
| Line Coverage | >= 70% | Minimum acceptable coverage |
| Cyclomatic Complexity (max) | <= 30 | Maintainability limit |
| Critical Dependency Vulns | 0 | No vulnerable deps in production |

### 7.2 Warning Thresholds (Build Passes with Warnings)

| Metric | Threshold | Action |
|--------|-----------|--------|
| Medium Security Issues | <= 5 | Review and plan fix |
| Line Coverage | >= 80% | Target, not required |
| Branch Coverage | >= 70% | Target, not required |
| Tech Debt | <= 10 days | Flag for attention |
| Code Duplication | <= 5% | Review duplicates |
| Outdated Dependencies | <= 20% | Plan upgrades |

---

## 8. Implementation Plan

### Week 130

1. [ ] Create `scripts/generate-quality-report.py`
2. [ ] Create `scripts/check-quality-gate.py`
3. [ ] Create `scripts/generate-comparison.py`
4. [ ] Set up GitHub Actions for Stack A
5. [ ] Set up GitHub Actions for Stack B

### Week 131

1. [ ] Add MarQed API endpoints for quality reports
2. [ ] Create quality comparison dashboard
3. [ ] Add trend tracking
4. [ ] Integrate with existing quality services

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
