# QualityGateService Usage Guide

## Overview

The **QualityGateService** provides centralized quality checking across all work types (MAINTENANCE, NEW_FEATURE, BUG, ENHANCEMENT, TESTING). It enforces 28 best practice checks organized into 8 categories.

**Version**: 1.0 (Week 11)
**Status**: Production Ready
**Coverage**: 28 best practice checks

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Check Categories](#check-categories)
4. [Configuration](#configuration)
5. [Workflow Integration](#workflow-integration)
6. [Interpreting Results](#interpreting-results)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```typescript
import QualityGateService from '../services/qualityGateService';
```

### Simplest Usage

```typescript
// Create service with default configuration (all checks enabled)
const qualityGateService = new QualityGateService();

// Run post-implementation check
const result = await qualityGateService.checkPostImplementation({
  scope: 'full_codebase'
});

// Check if quality gates passed
if (!result.passed) {
  console.log(`❌ Quality gates failed: ${result.summary.totalViolations} violations`);
  console.log(`Overall score: ${result.bestPracticeScore.totalScore}%`);
}
```

---

## Basic Usage

### Pre-Implementation Check

Run **before** writing code during planning phase:

```typescript
const qualityGateService = new QualityGateService();

const preCheck = await qualityGateService.checkPreImplementation({
  scope: 'module',
  modulePath: 'src/features/new-dashboard'
});

// Pre-implementation checks are lightweight
// Currently returns empty findings (future: analyze existing patterns)
console.log(`Pre-check complete in ${preCheck.metadata.executionTime}ms`);
```

### Post-Implementation Check

Run **after** writing code, before commit:

```typescript
const qualityGateService = new QualityGateService();

const postCheck = await qualityGateService.checkPostImplementation({
  scope: 'specific_files',
  targetFiles: [
    'src/features/dashboard/DashboardService.ts',
    'src/features/dashboard/DashboardController.ts'
  ]
});

if (postCheck.blocking) {
  throw new Error('Quality gates BLOCKED - fix violations before committing');
}

console.log(`Quality Score: ${postCheck.bestPracticeScore.totalScore}%`);
```

---

## Check Categories

The service runs **28 best practice checks** across **8 categories**:

### 1. SIG-TOP-10 (3 checks)

Software Improvement Group's 10 guidelines for maintainability:

```typescript
// Enabled by default
const result = await service.checkPostImplementation({ scope: 'full_codebase' });

console.log(`SIG Compliance: ${result.bestPracticeScore.sigCompliance.overall}%`);
console.log(`Violations:
  - High Complexity: ${result.bestPracticeScore.sigCompliance.violations.simpleUnits}
  - Code Duplication: ${result.bestPracticeScore.sigCompliance.violations.writeOnce}
  - Too Many Parameters: ${result.bestPracticeScore.sigCompliance.violations.smallInterfaces}
`);
```

**Checks**:
- SIG #2: Write Simple Units (cyclomatic complexity ≤ 10)
- SIG #3: Write Code Once (DRY, duplication ≤ 3%)
- SIG #4: Keep Unit Interfaces Small (≤ 4 parameters)

### 2. SOLID Principles (3 checks)

Object-oriented design principles:

```typescript
console.log(`SOLID Compliance: ${result.bestPracticeScore.solidCompliance.overall}%`);
console.log(`Violations:
  - Single Responsibility: ${result.bestPracticeScore.solidCompliance.violations.srp}
  - Open/Closed: ${result.bestPracticeScore.solidCompliance.violations.ocp}
  - Liskov Substitution: ${result.bestPracticeScore.solidCompliance.violations.lsp}
`);
```

**Checks**:
- Single Responsibility Principle
- Open/Closed Principle
- Liskov Substitution Principle

### 3. GRASP Principles (2 checks)

General Responsibility Assignment Software Patterns:

```typescript
console.log(`GRASP Compliance: ${result.bestPracticeScore.graspCompliance.overall}%`);
console.log(`Violations:
  - Information Expert: ${result.bestPracticeScore.graspCompliance.violations.informationExpert}
  - High Cohesion: ${result.bestPracticeScore.graspCompliance.violations.highCohesion}
`);
```

**Checks**:
- Information Expert (data and operations together)
- High Cohesion (related functionality together)

### 4. TDD (3 checks)

Test-Driven Development compliance:

```typescript
console.log(`TDD Compliance: ${result.bestPracticeScore.tddCompliance.overall}%`);
console.log(`Violations:
  - No Tests: ${result.bestPracticeScore.tddCompliance.violations.noTests}
  - Tests After Code: ${result.bestPracticeScore.tddCompliance.violations.testAfterCode}
  - Coverage Decrease: ${result.bestPracticeScore.tddCompliance.violations.coverageDecrease}
`);
```

**Checks**:
- Production code has tests
- Tests written before implementation (Red-Green-Refactor)
- Coverage doesn't decrease

### 5. Testing Patterns (6 checks)

Test quality and structure:

```typescript
console.log(`Testing Patterns: ${result.bestPracticeScore.testingPatternsCompliance.overall}%`);
console.log(`Violations:
  - AAA Pattern: ${result.bestPracticeScore.testingPatternsCompliance.violations.aaaPattern}
  - F.I.R.S.T: ${result.bestPracticeScore.testingPatternsCompliance.violations.firstPrinciples}
  - Test Pyramid: ${result.bestPracticeScore.testingPatternsCompliance.violations.testPyramid}
  - Given-When-Then: ${result.bestPracticeScore.testingPatternsCompliance.violations.givenWhenThen}
`);
```

**Checks**:
- AAA Pattern (Arrange-Act-Assert)
- F.I.R.S.T - Fast (tests run quickly)
- F.I.R.S.T - Independent (no dependencies between tests)
- F.I.R.S.T - Repeatable (deterministic results)
- Test Pyramid (70:20:10 ratio Unit:Integration:E2E)
- Given-When-Then (BDD structure)

### 6. Design Patterns (5 checks)

Gang of Four patterns:

```typescript
console.log(`Design Patterns: ${result.bestPracticeScore.designPatternsCompliance.overall}%`);
console.log(`Violations:
  - Factory Pattern: ${result.bestPracticeScore.designPatternsCompliance.violations.factoryPattern}
  - Builder Pattern: ${result.bestPracticeScore.designPatternsCompliance.violations.builderPattern}
  - Strategy Pattern: ${result.bestPracticeScore.designPatternsCompliance.violations.strategyPattern}
  - Observer Pattern: ${result.bestPracticeScore.designPatternsCompliance.violations.observerPattern}
  - Singleton Misuse: ${result.bestPracticeScore.designPatternsCompliance.violations.singletonPattern}
`);
```

**Checks**:
- Factory Pattern missing (tight coupling)
- Builder Pattern missing (complex constructors)
- Strategy Pattern missing (switch statements)
- Observer Pattern missing (polling instead of events)
- Singleton Pattern misuse (global state)

### 7. Clean Code (5 checks)

Code cleanliness principles:

```typescript
console.log(`Clean Code: ${result.bestPracticeScore.cleanCodeCompliance.overall}%`);
console.log(`Violations:
  - YAGNI: ${result.bestPracticeScore.cleanCodeCompliance.violations.yagni}
  - KISS: ${result.bestPracticeScore.cleanCodeCompliance.violations.kiss}
  - Boy Scout Rule: ${result.bestPracticeScore.cleanCodeCompliance.violations.boyScoutRule}
  - Magic Numbers: ${result.bestPracticeScore.cleanCodeCompliance.violations.magicNumbers}
  - Meaningful Names: ${result.bestPracticeScore.cleanCodeCompliance.violations.meaningfulNames}
`);
```

**Checks**:
- YAGNI (You Aren't Gonna Need It - unused code)
- KISS (Keep It Simple, Stupid - over-engineering)
- Boy Scout Rule (leave code cleaner than found)
- Magic Numbers (hardcoded constants)
- Meaningful Names (clear variable/function names)

### 8. Law of Demeter (1 check)

Principle of Least Knowledge:

```typescript
console.log(`Law of Demeter violations: ${result.bestPracticeScore.lawOfDemeter.violations}`);
```

**Checks**:
- Method call chains (a.getB().getC())

---

## Configuration

### Default Configuration

```typescript
// All checks enabled, blocking on critical violations
const service = new QualityGateService();
```

Equivalent to:

```typescript
const service = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: true,
    testingPatterns: true,
    designPatterns: true,
    cleanCode: true,
    lawOfDemeter: true
  },
  blockingRules: {
    blockOnCritical: true,              // Block any critical violation
    blockOnCoverageDecrease: true,      // Block if coverage decreases
    blockOnNoTests: false,              // Warning only for missing tests
    minimumScore: undefined             // No minimum score threshold
  },
  severityThresholds: {
    complexity: {
      low: 10,     // SIG guideline
      medium: 15,
      high: 20
    },
    duplication: {
      low: 3,      // SIG guideline: 3%
      medium: 5,
      high: 10
    }
  }
});
```

### Selective Checks

Enable only specific check categories:

```typescript
const architectureService = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: true,
    tdd: false,                // Skip TDD checks
    testingPatterns: false,    // Skip testing pattern checks
    designPatterns: true,
    cleanCode: true,
    lawOfDemeter: true
  }
});
```

### Blocking Rules

Control when to block commits:

```typescript
// Strict blocking
const strictService = new QualityGateService({
  blockingRules: {
    blockOnCritical: true,
    blockOnCoverageDecrease: true,
    blockOnNoTests: true,        // Block if no tests exist
    minimumScore: 80             // Block if score < 80%
  }
});

// Lenient (warnings only)
const lenientService = new QualityGateService({
  blockingRules: {
    blockOnCritical: false,
    blockOnCoverageDecrease: false,
    blockOnNoTests: false,
    minimumScore: undefined
  }
});
```

### Severity Thresholds

Adjust what counts as low/medium/high severity:

```typescript
const customService = new QualityGateService({
  severityThresholds: {
    complexity: {
      low: 8,      // Stricter than SIG (10)
      medium: 12,
      high: 15
    },
    duplication: {
      low: 2,      // Stricter than SIG (3%)
      medium: 4,
      high: 8
    }
  }
});
```

---

## Workflow Integration

### MAINTENANCE Workflow

```typescript
// backend/agents/workflows/codeMaintenanceAgent.ts

import QualityGateService from '../services/qualityGateService';

async function executeAnalysisStage(request, agent) {
  const qualityGateService = new QualityGateService(); // Default: blocking

  const qualityGateResult = await qualityGateService.checkPostImplementation({
    scope: request.scope,
    targetFiles: request.targetFiles,
    modulePath: request.modulePath,
    thresholds: request.thresholds
  });

  if (qualityGateResult.blocking) {
    throw new Error('MAINTENANCE: Quality gates blocked - fix critical violations');
  }

  return {
    bestPracticeScore: qualityGateResult.bestPracticeScore,
    findings: qualityGateResult.findings
  };
}
```

### NEW_FEATURE Workflow

```typescript
// backend/agents/workflows/newFeatureWorkflow.ts

import QualityGateService from '../services/qualityGateService';

async function executeNewFeatureWorkflow(request) {
  // Non-blocking configuration for new features
  const qualityGateService = new QualityGateService({
    blockingRules: {
      blockOnCritical: false,           // Warnings only
      blockOnCoverageDecrease: false,
      blockOnNoTests: false,
      minimumScore: undefined
    }
  });

  // Pre-implementation check
  const preChecks = await qualityGateService.checkPreImplementation({
    scope: request.modulePath ? 'module' : 'specific_files',
    targetFiles: request.targetFiles,
    modulePath: request.modulePath
  });

  // ... implement feature ...

  // Post-implementation check
  const postChecks = await qualityGateService.checkPostImplementation({
    scope: request.modulePath ? 'module' : 'specific_files',
    targetFiles: request.targetFiles,
    modulePath: request.modulePath
  });

  return {
    qualityGates: {
      pre: preChecks,
      post: postChecks,
      overallScore: (preChecks.bestPracticeScore.totalScore + postChecks.bestPracticeScore.totalScore) / 2,
      blocking: postChecks.blocking
    }
  };
}
```

### BUG Workflow

```typescript
// backend/agents/workflows/bugWorkflow.ts

import QualityGateService from '../services/qualityGateService';

async function executeBugWorkflow(bugReport) {
  // BLOCKING configuration for bug fixes
  const qualityGateService = new QualityGateService({
    blockingRules: {
      blockOnCritical: true,
      blockOnCoverageDecrease: true,
      blockOnNoTests: true,          // CRITICAL: Regression test required!
      minimumScore: undefined
    }
  });

  const postChecks = await qualityGateService.checkPostImplementation({
    scope: bugReport.modulePath ? 'module' : 'specific_files',
    targetFiles: bugReport.targetFiles,
    modulePath: bugReport.modulePath
  });

  if (postChecks.blocking) {
    throw new Error('BUG: Quality gates blocked - regression test required!');
  }

  return { qualityGates: postChecks };
}
```

---

## Interpreting Results

### QualityGateResult Structure

```typescript
interface QualityGateResult {
  passed: boolean;              // True if all checks pass
  blocking: boolean;            // True if should block commit
  bestPracticeScore: {
    totalScore: number;         // 0-100% overall score
    sigCompliance: { overall: number; violations: {...} };
    solidCompliance: { overall: number; violations: {...} };
    graspCompliance: { overall: number; violations: {...} };
    tddCompliance: { overall: number; violations: {...} };
    testingPatternsCompliance: { overall: number; violations: {...} };
    designPatternsCompliance: { overall: number; violations: {...} };
    cleanCodeCompliance: { overall: number; violations: {...} };
    lawOfDemeter: { violations: number };
  };
  findings: QualityFinding[];   // Detailed violations
  summary: {
    totalViolations: number;
    criticalViolations: number;
    highViolations: number;
    mediumViolations: number;
    lowViolations: number;
  };
  metadata: {
    executionTime: number;      // Milliseconds
    timestamp: Date;
    scope: string;
  };
}
```

### Reading Findings

Each finding contains:

```typescript
interface QualityFinding {
  id: string;                   // e.g., "DESIGN-003"
  category: 'dependency' | 'code_smell' | 'security' | 'performance' | 'test' | 'documentation';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;                // Human-readable title
  description: string;          // What's wrong
  location: string;             // File:line
  recommendation: string;       // How to fix
  estimatedEffort: number;      // Story points
  riskIfNotFixed: 'high' | 'medium' | 'low';
  autoFixable: boolean;
  bestPractice?: string;        // e.g., "Design Patterns: Strategy Pattern"
}
```

### Example Output

```typescript
const result = await service.checkPostImplementation({ scope: 'full_codebase' });

console.log(`
Quality Gate Results:
=====================
Status: ${result.passed ? '✅ PASSED' : '❌ FAILED'}${result.blocking ? ' (BLOCKING)' : ''}
Overall Score: ${result.bestPracticeScore.totalScore}%

Violations: ${result.summary.totalViolations} total
  - Critical: ${result.summary.criticalViolations}
  - High: ${result.summary.highViolations}
  - Medium: ${result.summary.mediumViolations}
  - Low: ${result.summary.lowViolations}

Category Scores:
  - SIG-TOP-10:        ${result.bestPracticeScore.sigCompliance.overall}%
  - SOLID:             ${result.bestPracticeScore.solidCompliance.overall}%
  - GRASP:             ${result.bestPracticeScore.graspCompliance.overall}%
  - TDD:               ${result.bestPracticeScore.tddCompliance.overall}%
  - Testing Patterns:  ${result.bestPracticeScore.testingPatternsCompliance.overall}%
  - Design Patterns:   ${result.bestPracticeScore.designPatternsCompliance.overall}%
  - Clean Code:        ${result.bestPracticeScore.cleanCodeCompliance.overall}%

Execution Time: ${result.metadata.executionTime}ms
`);

// Print detailed findings
result.findings.forEach(finding => {
  console.log(`
${finding.severity.toUpperCase()}: ${finding.title}
  Location: ${finding.location}
  ${finding.description}
  Recommendation: ${finding.recommendation}
  Effort: ${finding.estimatedEffort} story points
  `);
});
```

---

## Common Patterns

### Pattern 1: Pre-commit Check

```typescript
async function preCommitCheck(changedFiles: string[]) {
  const service = new QualityGateService();

  const result = await service.checkPostImplementation({
    scope: 'specific_files',
    targetFiles: changedFiles
  });

  if (result.blocking) {
    console.error('❌ Pre-commit check FAILED');
    console.error(`Fix ${result.summary.criticalViolations} critical violations before committing`);
    process.exit(1);
  }

  console.log('✅ Pre-commit check PASSED');
}
```

### Pattern 2: CI/CD Integration

```typescript
async function ciQualityCheck() {
  const service = new QualityGateService({
    blockingRules: {
      blockOnCritical: true,
      blockOnCoverageDecrease: true,
      blockOnNoTests: true,
      minimumScore: 75  // Require 75% in CI
    }
  });

  const result = await service.checkPostImplementation({
    scope: 'full_codebase'
  });

  // Write results to file for CI artifacts
  await fs.writeFile('quality-report.json', JSON.stringify(result, null, 2));

  if (result.blocking) {
    throw new Error('CI quality check failed');
  }
}
```

### Pattern 3: Progressive Enhancement

```typescript
// Week 10: Warnings only
const week10Service = new QualityGateService({
  blockingRules: { blockOnCritical: false, ... }
});

// Week 11: Block on critical
const week11Service = new QualityGateService({
  blockingRules: { blockOnCritical: true, ... }
});

// Week 12: Require minimum score
const week12Service = new QualityGateService({
  blockingRules: { blockOnCritical: true, minimumScore: 70 }
});
```

---

## Troubleshooting

### Issue: Too Many Violations

**Problem**: First run shows 50+ violations

**Solution**: Use progressive rollout
```typescript
// Step 1: Warnings only, track metrics
const service = new QualityGateService({
  blockingRules: { blockOnCritical: false }
});

// Step 2: After 1 week, block critical only
// Step 3: After 2 weeks, block high severity
// Step 4: After 4 weeks, require minimum score
```

### Issue: Checks Take Too Long

**Problem**: Quality checks take >30 seconds

**Solution**: Run selective checks during development
```typescript
// During development: Fast checks only
const devService = new QualityGateService({
  enabledChecks: {
    sig: true,
    solid: true,
    grasp: false,    // Disable slower checks
    tdd: true,
    testingPatterns: false,
    designPatterns: false,
    cleanCode: true,
    lawOfDemeter: false
  }
});

// In CI: All checks
const ciService = new QualityGateService(); // All enabled
```

### Issue: False Positives

**Problem**: Service reports violations incorrectly

**Solution**: Configure thresholds
```typescript
const service = new QualityGateService({
  severityThresholds: {
    complexity: {
      low: 15,     // Increase if your codebase legitimately needs higher complexity
      medium: 20,
      high: 30
    }
  }
});
```

---

## Next Steps

- **Configuration**: See [QUALITY_GATE_CONFIGURATION.md](./QUALITY_GATE_CONFIGURATION.md)
- **Extension**: See [QUALITY_GATE_EXTENSION.md](./QUALITY_GATE_EXTENSION.md)
- **Week 10 Summary**: See [WEEK_10_COMPLETE_SUMMARY.md](./WEEK_10_COMPLETE_SUMMARY.md)
- **Week 11 Summary**: See [WEEK_11_COMPLETE_SUMMARY.md](./WEEK_11_COMPLETE_SUMMARY.md)

---

**Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Production Ready
